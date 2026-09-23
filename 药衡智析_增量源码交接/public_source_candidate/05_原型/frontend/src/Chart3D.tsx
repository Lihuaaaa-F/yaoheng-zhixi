import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { Bar3DChart, Lines3DChart, Scatter3DChart } from 'echarts-gl/charts';
import { Grid3DComponent } from 'echarts-gl/components';
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 按需注册（2026-09-23 审查 SSE-2：全量 `import 'echarts-gl'` 把 globe/graphGL/flowGL
// 等未用图表全部打进首屏，GL 栈合计约 497KB）。
echarts.use([Bar3DChart, Scatter3DChart, Lines3DChart, Grid3DComponent, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, CanvasRenderer]);

/** WebGL 三维图表容器（scatter3D+lines3D/grid3D 用）：与 Chart 同生命周期语义，
 * 但对容器显式给高（3D 画布不会随内容自适应），并在卸载时释放 GL 资源。 */
export default function Chart3D({ option, label, height = 720, onClick, onHover }: {
    option: echarts.EChartsCoreOption;
    label: string;
    height?: number;
    onClick?: (event: any) => void;
    /** GL 系列原生 tooltip 在 echarts 5.6+ 失效（echarts-gl 兼容缺陷），
     * 用 GL 拾取事件 mouseover/mouseout 自渲染浮层：info=null 表示移出。 */
    onHover?: (info: { text: string; x: number; y: number } | null) => void;
}) {
    const ref = useRef<HTMLDivElement>(null), instance = useRef<echarts.ECharts | undefined>(undefined), optionSignature = useRef<string>('');
    useEffect(() => {
        if (!ref.current) return;
        const dom = ref.current;
        const chart = echarts.init(dom);
        instance.current = chart;
        // 测试/调试验证钩子：Playwright 可读取相机参数与 convertToPixel
        (window as any).__chart3d = (window as any).__chart3d ?? new Map();
        (window as any).__chart3d.set(dom, chart);
        const observer = new ResizeObserver(() => chart.resize());
        observer.observe(dom);
        // 光标在图谱区域内时，滚轮只缩放图谱、不再滚动页面（2026-09-24
        // 用户要求）。echarts-gl 的 wheel 处理不总是 preventDefault，
        // 这里在容器上原生兜底（必须 non-passive 才能 preventDefault）。
        const wheelGuard = (event: WheelEvent) => event.preventDefault();
        dom.addEventListener('wheel', wheelGuard, { passive: false });
        return () => {
            observer.disconnect();
            dom.removeEventListener('wheel', wheelGuard);
            (window as any).__chart3d?.delete(dom);
            chart.dispose(); instance.current = undefined;
        };
    }, []);
    useEffect(() => {
        const chart = instance.current; if (!chart) return;
        // 内容未变（如仅悬停浮层 state 变化）时跳过 notMerge 全量 setOption——
        // 否则每次 mouseover 都重建整个 WebGL 场景（2026-09-23 审查 SSE-13）。
        const signature = JSON.stringify(option);
        if (signature === optionSignature.current) return;
        optionSignature.current = signature;
        // Imported labels are untrusted text; never render chart tooltips as HTML.
        chart.setOption({ ...option, tooltip: { ...(option.tooltip as object), renderMode: 'richText', confine: true }, animation: false, textStyle: { fontFamily: '"Noto Sans CJK SC",sans-serif', fontSize: 12 } }, true);
    }, [option]);
    useEffect(() => { const chart = instance.current; if (!chart || !onClick) return; chart.on('click', onClick); return () => { chart.off('click', onClick); }; }, [onClick]);
    // GL 拾取悬停：echarts 把 GL 系列的 mouseover/mouseout 以 zr 事件抛出，
    // 事件参数带 componentType/seriesIndex/dataIndex/name；坐标取原始事件。
    useEffect(() => {
        const chart = instance.current;
        if (!chart || !onHover) return;
        const dom = ref.current!;
        const handle = (params: any) => {
            const ev = params.event?.event as MouseEvent | undefined;
            const kindMap: Record<string, string> = { 产品: '产品', 药材: '药材', 工序: '工序' };
            // GL 系列 mouseover 的 componentType 是 'series'（非 'scatter3D'），
            // 用 data.tooltip_kind 区分节点/边点：边点 name 是完整关系串。
            if (params.componentType === 'series' && params.name) {
                const kind = (params.data?.tooltip_kind as string) ?? '';
                const text = kind === '边' ? params.name : `${params.name}（${kind || ''}）`;
                const rect = dom.getBoundingClientRect();
                onHover({ text, x: (ev?.clientX ?? rect.left) - rect.left + 14, y: (ev?.clientY ?? rect.top) - rect.top + 10 });
            } else if (params.type === 'mouseout') {
                onHover(null);
            }
        };
        chart.on('mouseover', handle);
        chart.on('mouseout', () => onHover(null));
        return () => { chart.off('mouseover', handle); chart.off('mouseout'); };
    }, [onHover]);
    return <div className="chart chart-3d" ref={ref} role="img" aria-label={label} style={{ height, width: '100%' }} />;
}
