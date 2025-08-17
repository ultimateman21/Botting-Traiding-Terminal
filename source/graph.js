const graphDiv = document.getElementById('graph');

let candleLayout, volumeLayout, turnoverLayout, graphLayout;
let candleTrace, volumeTrace, turnoverTrace;
let candleId, volumeId, turnoverId;

const initGraph = (traceLayout, figData) => {
    candleLayout = traceLayout.find(trace => trace.name === 'Свеча');
    volumeLayout = traceLayout.find(trace => trace.name === 'Объём');
    turnoverLayout = traceLayout.find(trace => trace.name === 'Оборот');

    graphLayout = figData.layout;

    Plotly.newPlot(graphDiv, figData.data, figData.layout, {scrollZoom: true, responsive: true, locale: 'ru'});

    candleTrace = graphDiv.data.find(trace => trace.name === 'Свеча');
    candleId = graphDiv.data.indexOf(candleTrace);

    volumeTrace = graphDiv.data.find(trace => trace.name === 'Объём');
    volumeId = graphDiv.data.indexOf(volumeTrace);
    updateColors('Объём');

    if (graphDiv.data.find(trace => trace.name === 'Оборот')) {
        turnoverTrace = graphDiv.data.find(trace => trace.name === 'Оборот');
        turnoverId = graphDiv.data.indexOf(turnoverTrace);
        updateColors('Оборот');
    }
};

const updateGraphData = (dataSet) => {
    let newTraceData = [Object.assign({}, candleLayout, {x: dataSet.timestamp, open: dataSet.open,
                                          high: dataSet.high, low: dataSet.low, close: dataSet.close}),
                        Object.assign({}, volumeLayout, {x: dataSet.timestamp, y: dataSet.volume})];

    if ('turnover' in dataSet) {
        newTraceData.push(Object.assign({}, turnoverLayout, {x: dataSet.timestamp, y: dataSet.turnover}));
    }

    Plotly.react(graphDiv, newTraceData, graphLayout);

    candleTrace = graphDiv.data.find(trace => trace.name === 'Свеча');
    candleId = graphDiv.data.indexOf(candleTrace);

    volumeTrace = graphDiv.data.find(trace => trace.name === 'Объём');
    volumeId = graphDiv.data.indexOf(volumeTrace);
    updateColors('Объём');

    if (graphDiv.data.find(trace => trace.name === 'Оборот')) {
        turnoverTrace = graphDiv.data.find(trace => trace.name === 'Оборот');
        turnoverId = graphDiv.data.indexOf(turnoverTrace);
        updateColors('Оборот');
    }
};

const newCandle = (candle) => {
    if (!updateCandle(candle)) {
        let [time, open, high, low, close, volume, turnover] = candle;

        Plotly.extendTraces(graphDiv, {x: [[time]], open: [[open]], high: [[high]],
                            low: [[low]], close: [[close]]}, [candleId], 720);

        Plotly.extendTraces(graphDiv, {x: [[time]], y: [[volume]]}, [volumeId], 720);
        updateColors('Объём');

        if (graphDiv.data.find(trace => trace.name === 'Оборот')) {
            Plotly.extendTraces(graphDiv, {x: [[time]], y: [[turnover]]}, [turnoverId], 720);
            updateColors('Оборот');
        }
    }
};

const updateCandle = (candle) => {
    let [time, open, high, low, close, volume, turnover] = candle;
    let timeIndex = candleTrace.x.indexOf(time.toString());
    if (timeIndex !== -1) {
        candleTrace.open[timeIndex] = open;
        candleTrace.high[timeIndex] = high;
        candleTrace.low[timeIndex] = low;
        candleTrace.close[timeIndex] = close;
        volumeTrace.y[timeIndex] = volume;
        updateColors('Объём');

        if (graphDiv.data.find(trace => trace.name === 'Оборот')) {
            turnoverTrace.y[timeIndex] = turnover;
            updateColors('Оборот');
        }
        return true;
    }
    return false;
};

const updateColors = (name) => {
    let targetTrace = graphDiv.data.find(trace => trace.name === name);
    if (targetTrace) {
        let colors = candleTrace.open.map((open, i) => candleTrace.close[i] > open ? '#00cc96' : '#ef553b');
        Plotly.restyle(graphDiv, {'marker.color': [colors]}, graphDiv.data.indexOf(targetTrace));
    }
};

const clearGraph = () => {
    Plotly.react(graphDiv, [], graphLayout);
};

new QWebChannel(qt.webChannelTransport, function(channel) {
    let bridge = channel.objects.bridge;
    bridge.initGraph.connect(function(layout, data){
        initGraph(JSON.parse(layout), JSON.parse(data));
    });
    bridge.addDataSet.connect(function(set) {
        updateGraphData(JSON.parse(set));
    });
    bridge.addCandle.connect(function(candle) {
        newCandle(candle);
    });
    bridge.clearGraph.connect(function() {
        clearGraph();
    });
});