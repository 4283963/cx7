import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import ScatterPlot from './components/ScatterPlot.jsx'

const App = () => {
  const [loading, setLoading] = useState(false)
  const [allCandidates, setAllCandidates] = useState([])
  const [topPackages, setTopPackages] = useState([])
  const [topPackageIds, setTopPackageIds] = useState([])
  const [totalCandidates, setTotalCandidates] = useState(0)
  const [selectedPackage, setSelectedPackage] = useState(null)
  const [formData, setFormData] = useState({
    priceWeight: 0.5,
    discountWeight: 0.5,
    topN: 5,
    flightCount: 6,
    hotelCount: 5
  })

  const fetchSampleAndCalculate = useCallback(async () => {
    setLoading(true)
    try {
      const sampleRes = await axios.post('/api/v1/packages/sample')
      const sampleData = sampleRes.data

      const flights = sampleData.flights.slice(0, formData.flightCount)
      const hotels = sampleData.hotels.slice(0, formData.hotelCount)

      const requestData = {
        flights,
        hotels,
        time_window: sampleData.time_window,
        top_n: formData.topN,
        price_weight: formData.priceWeight,
        discount_weight: formData.discountWeight
      }

      const vizRes = await axios.post('/api/v1/packages/visualization', requestData)
      
      if (vizRes.data.success) {
        setAllCandidates(vizRes.data.all_candidates)
        setTopPackages(vizRes.data.top_packages)
        setTopPackageIds(vizRes.data.top_package_ids)
        setTotalCandidates(vizRes.data.total_candidates)
        if (vizRes.data.top_packages.length > 0) {
          setSelectedPackage(vizRes.data.top_packages[0])
        }
      }
    } catch (error) {
      console.error('计算出错:', error)
    } finally {
      setLoading(false)
    }
  }, [formData])

  useEffect(() => {
    fetchSampleAndCalculate()
  }, [fetchSampleAndCalculate])

  const handleSliderChange = (key, value) => {
    const numValue = parseFloat(value)
    if (key === 'priceWeight') {
      setFormData(prev => ({
        ...prev,
        priceWeight: numValue,
        discountWeight: parseFloat((1 - numValue).toFixed(2))
      }))
    } else if (key === 'discountWeight') {
      setFormData(prev => ({
        ...prev,
        discountWeight: numValue,
        priceWeight: parseFloat((1 - numValue).toFixed(2))
      }))
    } else {
      setFormData(prev => ({ ...prev, [key]: numValue }))
    }
  }

  const handlePointClick = (point) => {
    const pkg = topPackages.find(p => p.package_id === point.package_id)
    if (pkg) {
      setSelectedPackage(pkg)
    }
  }

  const bestPrice = allCandidates.length > 0 
    ? Math.min(...allCandidates.map(d => d.discounted_total_price)) 
    : 0
  
  const bestDiscount = allCandidates.length > 0
    ? Math.max(...allCandidates.map(d => d.total_discount_rate))
    : 0

  const avgPrice = allCandidates.length > 0
    ? allCandidates.reduce((sum, d) => sum + d.discounted_total_price, 0) / allCandidates.length
    : 0

  return (
    <div className="container">
      <header className="header">
        <h1>✈️ 动态打包折扣最优组合仿真工具</h1>
        <p>机票 + 酒店 智能推荐 · 多目标线性规划算法</p>
      </header>

      <div className="main-content">
        <div className="left-panel">
          <div className="card">
            <h2>⚙️ 参数设置</h2>
            
            <div className="form-group">
              <label>航班数量: {formData.flightCount} 个</label>
              <div className="slider-group">
                <input
                  type="range"
                  min="2"
                  max="10"
                  value={formData.flightCount}
                  onChange={(e) => handleSliderChange('flightCount', e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>酒店数量: {formData.hotelCount} 个</label>
              <div className="slider-group">
                <input
                  type="range"
                  min="2"
                  max="10"
                  value={formData.hotelCount}
                  onChange={(e) => handleSliderChange('hotelCount', e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Top N 推荐: {formData.topN} 个</label>
              <div className="slider-group">
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={formData.topN}
                  onChange={(e) => handleSliderChange('topN', e.target.value)}
                />
              </div>
            </div>

            <h3 style={{ fontSize: '1rem', margin: '20px 0 12px 0', color: '#555' }}>
              目标权重设置
            </h3>

            <div className="form-group">
              <label>价格权重</label>
              <div className="slider-group">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={formData.priceWeight}
                  onChange={(e) => handleSliderChange('priceWeight', e.target.value)}
                />
                <span className="slider-value">{(formData.priceWeight * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div className="form-group">
              <label>折扣权重</label>
              <div className="slider-group">
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={formData.discountWeight}
                  onChange={(e) => handleSliderChange('discountWeight', e.target.value)}
                />
                <span className="slider-value">{(formData.discountWeight * 100).toFixed(0)}%</span>
              </div>
            </div>

            <button 
              className="btn btn-primary"
              onClick={fetchSampleAndCalculate}
              disabled={loading}
            >
              {loading ? '计算中...' : '🔄 重新计算'}
            </button>
          </div>

          <div className="card" style={{ marginTop: '20px' }}>
            <h2>📊 统计概览</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-value">{totalCandidates}</div>
                <div className="stat-label">候选组合</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">¥{bestPrice.toLocaleString()}</div>
                <div className="stat-label">最低价格</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">{(bestDiscount * 100).toFixed(1)}%</div>
                <div className="stat-label">最高折扣</div>
              </div>
              <div className="stat-card">
                <div className="stat-value">¥{avgPrice.toFixed(0)}</div>
                <div className="stat-label">平均价格</div>
              </div>
            </div>
          </div>
        </div>

        <div className="right-panel">
          <div className="card">
            <h2>📈 价格 - 推荐指数散点图</h2>
            {loading ? (
              <div className="loading">加载中...</div>
            ) : (
              <ScatterPlot 
                data={allCandidates} 
                topPackageIds={topPackageIds}
                onPointClick={handlePointClick}
              />
            )}
          </div>

          <div className="card" style={{ marginTop: '20px' }}>
            <h2>🏆 Top {formData.topN} 推荐套餐</h2>
            {loading ? (
              <div className="loading">加载中...</div>
            ) : topPackages.length === 0 ? (
              <div className="empty-state">暂无符合条件的套餐</div>
            ) : (
              <div className="package-list">
                {topPackages.map((pkg) => (
                  <div 
                    key={pkg.package_id}
                    className={`package-card ${selectedPackage?.package_id === pkg.package_id ? 'active' : ''}`}
                    onClick={() => setSelectedPackage(pkg)}
                  >
                    <div className="package-title">
                      <span className="package-rank">{pkg.rank}</span>
                      {pkg.flight.flight_no} + {pkg.hotel.hotel_name}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span className="package-price">¥{pkg.discounted_total_price.toLocaleString()}</span>
                      <span className="package-discount">省 ¥{pkg.total_discount_amount.toFixed(0)}</span>
                    </div>
                    <div className="package-details">
                      <div>航班: {pkg.flight.departure_city} → {pkg.flight.arrival_city} | {pkg.flight.departure_date}</div>
                      <div>酒店: {pkg.hotel.city} | {pkg.hotel.check_in_date} ~ {pkg.hotel.check_out_date} ({pkg.stay_days}晚)</div>
                    </div>
                    <div className="package-score">
                      <span style={{ fontSize: '0.85rem', color: '#666', minWidth: '70px' }}>推荐指数</span>
                      <div className="score-bar">
                        <div 
                          className="score-fill" 
                          style={{ width: `${pkg.recommendation_score * 100}%` }}
                        ></div>
                      </div>
                      <span className="score-text">{(pkg.recommendation_score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
