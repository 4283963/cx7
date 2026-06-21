import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import ScatterPlot from './components/ScatterPlot.jsx'

const AIRLINE_OPTIONS = [
  { code: 'CA', name: '中国国航' },
  { code: 'MU', name: '东方航空' },
  { code: 'CZ', name: '南方航空' },
  { code: 'HU', name: '海南航空' },
  { code: '3U', name: '四川航空' },
  { code: 'ZH', name: '深圳航空' }
]

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
  
  const [fuelSurge, setFuelSurge] = useState({
    enabled: false,
    targetAirline: 'CA',
    priceIncreaseRate: 2.0,
    applyOnBooking: true
  })
  
  const [bookingModal, setBookingModal] = useState({
    visible: false,
    loading: false,
    result: null
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
        discount_weight: formData.discountWeight,
        fuel_surge: fuelSurge.enabled ? {
          enabled: true,
          target_airline: fuelSurge.targetAirline,
          price_increase_rate: fuelSurge.priceIncreaseRate,
          apply_on_booking: fuelSurge.applyOnBooking
        } : null
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
  }, [formData, fuelSurge])

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

  const handleFuelSurgeChange = (key, value) => {
    setFuelSurge(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const handleBooking = async (pkg) => {
    setBookingModal({
      visible: true,
      loading: true,
      result: null
    })
    
    try {
      const bookData = {
        package_id: pkg.package_id,
        flight: pkg.flight,
        hotel: pkg.hotel,
        quoted_price: pkg.discounted_total_price,
        fuel_surge: fuelSurge.enabled ? {
          enabled: true,
          target_airline: fuelSurge.targetAirline,
          price_increase_rate: fuelSurge.priceIncreaseRate,
          apply_on_booking: fuelSurge.applyOnBooking
        } : null
      }
      
      const response = await axios.post('/api/v1/packages/book', bookData)
      
      setBookingModal({
        visible: true,
        loading: false,
        result: response.data
      })
    } catch (error) {
      console.error('预订出错:', error)
      setBookingModal({
        visible: true,
        loading: false,
        result: {
          success: false,
          intercept_level: 'blocked',
          message: '预订请求失败，请稍后重试'
        }
      })
    }
  }

  const closeBookingModal = () => {
    setBookingModal({
      visible: false,
      loading: false,
      result: null
    })
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
            <h2>⛽ 燃油费突增模拟</h2>
            
            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={fuelSurge.enabled}
                  onChange={(e) => handleFuelSurgeChange('enabled', e.target.checked)}
                />
                <span>启用燃油费突增模拟</span>
              </label>
            </div>

            {fuelSurge.enabled && (
              <>
                <div className="form-group">
                  <label>目标航空公司</label>
                  <select
                    value={fuelSurge.targetAirline}
                    onChange={(e) => handleFuelSurgeChange('targetAirline', e.target.value)}
                  >
                    {AIRLINE_OPTIONS.map(airline => (
                      <option key={airline.code} value={airline.code}>
                        {airline.code} - {airline.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>价格涨幅: {(fuelSurge.priceIncreaseRate * 100).toFixed(0)}%</label>
                  <div className="slider-group">
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.1"
                      value={fuelSurge.priceIncreaseRate}
                      onChange={(e) => handleFuelSurgeChange('priceIncreaseRate', parseFloat(e.target.value))}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={fuelSurge.applyOnBooking}
                      onChange={(e) => handleFuelSurgeChange('applyOnBooking', e.target.checked)}
                    />
                    <span>购买时触发价格变动拦截</span>
                  </label>
                </div>

                <div className="surge-warning">
                  ⚠️ 启用后，{fuelSurge.targetAirline}航空的机票价格将上涨 {(fuelSurge.priceIncreaseRate * 100).toFixed(0)}%，
                  模拟闭环定价系统误判场景
                </div>
              </>
            )}
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
                    className={`package-card ${selectedPackage?.package_id === pkg.package_id ? 'active' : ''} ${pkg.fuel_surge_applied ? 'has-surge' : ''}`}
                    onClick={() => setSelectedPackage(pkg)}
                  >
                    <div className="package-title">
                      <span className="package-rank">{pkg.rank}</span>
                      {pkg.flight.flight_no} + {pkg.hotel.hotel_name}
                      {pkg.fuel_surge_applied && (
                        <span className="fuel-surge-badge">⛽ 燃油费</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
                      <span className="package-price">
                        ¥{pkg.discounted_total_price.toLocaleString()}
                      </span>
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
                    <button 
                      className="btn-book"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleBooking(pkg)
                      }}
                    >
                      立即购买
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {bookingModal.visible && (
        <div className="modal-overlay" onClick={closeBookingModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            {bookingModal.loading ? (
              <div className="booking-loading">
                <div className="spinner"></div>
                <p>正在确认价格...</p>
                <p className="booking-subtext">闭环定价系统实时校验中</p>
              </div>
            ) : bookingModal.result ? (
              <div className={`booking-result booking-${bookingModal.result.intercept_level}`}>
                <div className="booking-icon">
                  {bookingModal.result.intercept_level === 'none' && '✅'}
                  {bookingModal.result.intercept_level === 'warning' && '⚠️'}
                  {bookingModal.result.intercept_level === 'downgraded' && '🔄'}
                  {bookingModal.result.intercept_level === 'blocked' && '🚫'}
                </div>
                
                <h3 className="booking-title">
                  {bookingModal.result.intercept_level === 'none' && '预订成功'}
                  {bookingModal.result.intercept_level === 'warning' && '价格变动提醒'}
                  {bookingModal.result.intercept_level === 'downgraded' && '交易降级处理'}
                  {bookingModal.result.intercept_level === 'blocked' && '交易已拦截'}
                </h3>
                
                <p className="booking-message">{bookingModal.result.message}</p>
                
                {bookingModal.result.surge_triggered && (
                  <div className="surge-detail">
                    <div className="surge-header">
                      <span>⛽ 燃油费突增影响</span>
                      <span className="surge-airline">{bookingModal.result.affected_airline}航空</span>
                    </div>
                    <div className="price-compare">
                      <div className="price-item">
                        <span className="price-label">原始价格</span>
                        <span className="price-value old">¥{bookingModal.result.original_price.toLocaleString()}</span>
                      </div>
                      <div className="price-arrow">→</div>
                      <div className="price-item">
                        <span className="price-label">当前价格</span>
                        <span className="price-value new">¥{bookingModal.result.final_price.toLocaleString()}</span>
                      </div>
                    </div>
                    <div className="price-change">
                      涨幅 <span className={`change-rate ${bookingModal.result.price_change_rate > 0.3 ? 'danger' : bookingModal.result.price_change_rate > 0.05 ? 'warning' : 'normal'}`}>
                        +{(bookingModal.result.price_change_rate * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                )}
                
                {bookingModal.result.downgraded_alternative && (
                  <div className="downgrade-section">
                    <h4>💡 推荐替代方案</h4>
                    <p>{bookingModal.result.downgraded_alternative.description}</p>
                    <div className="airline-suggestions">
                      {bookingModal.result.downgraded_alternative.suggested_airlines?.map(airline => (
                        <span key={airline} className="airline-tag">{airline}</span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="booking-actions">
                  <button className="btn btn-secondary" onClick={closeBookingModal}>
                    {bookingModal.result.success ? '确定' : '我知道了'}
                  </button>
                  {bookingModal.result.intercept_level === 'downgraded' && (
                    <button className="btn btn-primary">
                      接受新价格
                    </button>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
