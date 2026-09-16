import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { LineChart, BarChart, PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
echarts.use([LineChart, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);
export default function Chart({ option, label }: {
    option: echarts.EChartsCoreOption;
    label: string;
}) {
    const ref = useRef<HTMLDivElement>(null), instance = useRef<echarts.ECharts | undefined>(undefined);
    useEffect(() => { if (!ref.current)
        return; const chart = echarts.init(ref.current); instance.current = chart; const observer = new ResizeObserver(() => chart.resize()); observer.observe(ref.current); return () => { observer.disconnect(); chart.dispose(); instance.current = undefined; }; }, []);
    useEffect(() => { instance.current?.setOption({ ...option, animation: false, textStyle: { fontFamily: '"Noto Sans CJK SC",sans-serif', fontSize: 12 } }, true); }, [option]);
    return <div className="chart" ref={ref} role="img" aria-label={label}/>;
}
