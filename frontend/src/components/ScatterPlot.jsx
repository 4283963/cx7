import React, { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'

const ScatterPlot = ({ data = [], topPackageIds = [], onPointClick }) => {
  const svgRef = useRef(null)
  const containerRef = useRef(null)
  const [tooltip, setTooltip] = useState({ visible: false, x: 0, y: 0, data: null })

  useEffect(() => {
    if (!data || data.length === 0 || !svgRef.current || !containerRef.current) return

    const container = containerRef.current
    const width = container.clientWidth
    const height = container.clientHeight
    const margin = { top: 40, right: 40, bottom: 60, left: 70 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    const xScale = d3.scaleLinear()
      .domain(d3.extent(data, d => d.discounted_total_price)).nice()
      .range([0, innerWidth])

    const yScale = d3.scaleLinear()
      .domain([0, 1])
      .range([innerHeight, 0])

    const xAxis = d3.axisBottom(xScale)
      .ticks(8)
      .tickFormat(d => `¥${d.toLocaleString()}`)

    const yAxis = d3.axisLeft(yScale)
      .ticks(5)
      .tickFormat(d => `${(d * 100).toFixed(0)}%`)

    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .style('font-size', '11px')
      .style('fill', '#666')

    g.append('g')
      .attr('class', 'y-axis')
      .call(yAxis)
      .selectAll('text')
      .style('font-size', '11px')
      .style('fill', '#666')

    g.selectAll('.x-axis path, .y-axis path, .x-axis line, .y-axis line')
      .style('stroke', '#ddd')

    g.append('text')
      .attr('class', 'x-label')
      .attr('x', innerWidth / 2)
      .attr('y', innerHeight + 45)
      .attr('text-anchor', 'middle')
      .style('font-size', '13px')
      .style('font-weight', '600')
      .style('fill', '#555')
      .text('套餐价格（元）')

    g.append('text')
      .attr('class', 'y-label')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerHeight / 2)
      .attr('y', -50)
      .attr('text-anchor', 'middle')
      .style('font-size', '13px')
      .style('font-weight', '600')
      .style('fill', '#555')
      .text('推荐指数')

    const gridLines = g.append('g').attr('class', 'grid')
    
    gridLines.selectAll('.grid-line-x')
      .data(yScale.ticks(5))
      .enter()
      .append('line')
      .attr('class', 'grid-line-x')
      .attr('x1', 0)
      .attr('x2', innerWidth)
      .attr('y1', d => yScale(d))
      .attr('y2', d => yScale(d))
      .style('stroke', '#eee')
      .style('stroke-dasharray', '3,3')

    const topSet = new Set(topPackageIds)

    const points = g.selectAll('.dot')
      .data(data)
      .enter()
      .append('circle')
      .attr('class', 'dot')
      .attr('cx', d => xScale(d.discounted_total_price))
      .attr('cy', d => yScale(d.recommendation_score))
      .attr('r', d => topSet.has(d.package_id) ? 9 : 5)
      .style('fill', d => {
        if (topSet.has(d.package_id)) {
          return d.is_pareto_optimal ? '#e74c3c' : '#667eea'
        }
        return d.is_pareto_optimal ? '#f39c12' : '#bbb'
      })
      .style('stroke', d => topSet.has(d.package_id) ? '#fff' : 'none')
      .style('stroke-width', d => topSet.has(d.package_id) ? 2.5 : 0)
      .style('cursor', 'pointer')
      .style('opacity', d => topSet.has(d.package_id) ? 1 : 0.6)
      .on('mouseover', function(event, d) {
        d3.select(this)
          .transition()
          .duration(150)
          .attr('r', topSet.has(d.package_id) ? 12 : 8)
        
        const rect = container.getBoundingClientRect()
        setTooltip({
          visible: true,
          x: event.clientX - rect.left + 15,
          y: event.clientY - rect.top - 10,
          data: d
        })
      })
      .on('mousemove', function(event, d) {
        const rect = container.getBoundingClientRect()
        setTooltip(prev => ({
          ...prev,
          x: event.clientX - rect.left + 15,
          y: event.clientY - rect.top - 10
        }))
      })
      .on('mouseout', function(event, d) {
        d3.select(this)
          .transition()
          .duration(150)
          .attr('r', topSet.has(d.package_id) ? 9 : 5)
        
        setTooltip({ visible: false, x: 0, y: 0, data: null })
      })
      .on('click', function(event, d) {
        if (onPointClick) {
          onPointClick(d)
        }
      })

    points.filter(d => topSet.has(d.package_id))
      .raise()

    const defs = svg.append('defs')
    
    const gradient = defs.append('radialGradient')
      .attr('id', 'glow-gradient')
      .attr('cx', '50%')
      .attr('cy', '50%')
      .attr('r', '50%')
    
    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', '#667eea')
      .attr('stop-opacity', 0.3)
    
    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', '#667eea')
      .attr('stop-opacity', 0)

  }, [data, topPackageIds, onPointClick])

  return (
    <div className="scatter-plot-container" ref={containerRef}>
      <svg ref={svgRef}></svg>
      {tooltip.visible && tooltip.data && (
        <div 
          className="tooltip"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          <h4>套餐 {tooltip.data.package_id}</h4>
          <p>价格: ¥{tooltip.data.discounted_total_price.toLocaleString()}</p>
          <p>原价: ¥{tooltip.data.original_total_price.toLocaleString()}</p>
          <p>折扣: {(tooltip.data.total_discount_rate * 100).toFixed(1)}%</p>
          <p>推荐指数: {(tooltip.data.recommendation_score * 100).toFixed(1)}%</p>
          <p>住宿: {tooltip.data.stay_days} 晚</p>
          {tooltip.data.is_pareto_optimal && (
            <p style={{ color: '#2ecc71', fontWeight: 600 }}>★ 帕累托最优</p>
          )}
        </div>
      )}
      <div className="legend">
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#e74c3c' }}></span>
          <span>Top推荐 (最优)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#667eea' }}></span>
          <span>Top推荐</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#f39c12' }}></span>
          <span>帕累托最优</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ background: '#bbb' }}></span>
          <span>其他候选</span>
        </div>
      </div>
    </div>
  )
}

export default ScatterPlot
