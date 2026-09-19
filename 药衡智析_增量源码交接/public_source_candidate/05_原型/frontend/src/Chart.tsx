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
    const ref = useRef<HTMLDivElement>(null), instance = useRef<echarts.ECharts | undefined>(undefined);
    useEffect(() => { if (!ref.current)
        return; const chart = echarts.init(ref.current); instance.current = chart; const observer = new ResizeObserver(() => chart.resize()); observer.observe(ref.current); return () => { observer.disconnect(); chart.dispose(); instance.current = undefined; }; }, []);
    useEffect(() => { instance.current?.setOption({ ...option, animation: false, textStyle: { fontFamily: '"Noto Sans CJK SC",sans-serif', fontSize: 12 } }, true); }, [option]);
    useEffect(() => { const chart = instance.current; if (!chart || !onClick) return; chart.on('click', onClick); return () => {chart.off('click', onClick)}; }, [onClick]);
    return <div className="chart" ref={ref} role="img" aria-label={label}/>;
}
