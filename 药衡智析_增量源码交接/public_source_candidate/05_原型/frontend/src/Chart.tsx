import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { LineChart, BarChart, PieChart, HeatmapChart, GraphChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
echarts.use([LineChart, BarChart, PieChart, HeatmapChart, GraphChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, CanvasRenderer]);
export default function Chart({ option, label, onClick }: {
    option: echarts.EChartsCoreOption;
    label: string;
    onClick?: (event: any) => void;
}) {
    const ref = useRef<HTMLDivElement>(null), instance = useRef<echarts.ECharts | undefined>(undefined), optionSignature = useRef<string>('');
    useEffect(() => { if (!ref.current)
        return; const chart = echarts.init(ref.current); instance.current = chart; const observer = new ResizeObserver(() => chart.resize()); observer.observe(ref.current); return () => { observer.disconnect(); chart.dispose(); instance.current = undefined; }; }, []);
    useEffect(() => {
        const chart = instance.current; if (!chart) return;
        // 调用方多为内联 option 字面量：父组件无关 state 变化也会生成新对象身份。
        // 内容未变时跳过 notMerge 全量重设，避免整图无谓重绘（2026-09-23 审查 SSE-12）。
        const signature = JSON.stringify(option);
        if (signature === optionSignature.current) return;
        optionSignature.current = signature;
        chart.setOption({ ...option, animation: false, textStyle: { fontFamily: '"Noto Sans CJK SC",sans-serif', fontSize: 12 } }, true);
    }, [option]);
    useEffect(() => { const chart = instance.current; if (!chart || !onClick) return; chart.on('click', onClick); return () => {chart.off('click', onClick)}; }, [onClick]);
    return <div className="chart" ref={ref} role="img" aria-label={label}/>;
}
