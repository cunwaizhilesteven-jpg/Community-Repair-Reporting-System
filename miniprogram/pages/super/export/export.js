/**
 * 数据导出页面
 * ==============
 * 超级管理员导出工单数据为Excel
 *
 * 功能：
 * - 选择导出时间范围
 * - 选择工单状态筛选
 * - 下载Excel文件
 *
 * 注意：
 * 小程序无法直接下载文件，需要：
 * 1. 调用后端接口获取下载链接
 * 2. 或者通过复制链接让用户在浏览器中下载
 */

const app = getApp()

Page({
  data: {
    // 导出配置
    exportConfig: {
      startDate: '',
      endDate: '',
      status: ''
    },
    // 状态选项
    statusOptions: [
      { value: '', label: '全部状态' },
      { value: 'pending', label: '待审核' },
      { value: 'assigned', label: '已分配' },
      { value: 'processing', label: '处理中' },
      { value: 'completed', label: '已完成' },
      { value: 'evaluated', label: '已评价' }
    ],
    statusIndex: 0,
    // 导出状态
    exporting: false,
    // 导出历史
    exportHistory: []
  },

  onLoad() {
    // 设置默认日期范围（最近30天）
    const today = this.formatDate(new Date())
    const thirtyDaysAgo = this.formatDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))

    this.setData({
      'exportConfig.startDate': thirtyDaysAgo,
      'exportConfig.endDate': today
    })
  },

  /**
   * 格式化日期为 YYYY-MM-DD
   */
  formatDate(date) {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  },

  /**
   * 开始日期变化
   */
  onStartDateChange(e) {
    this.setData({
      'exportConfig.startDate': e.detail.value
    })
  },

  /**
   * 结束日期变化
   */
  onEndDateChange(e) {
    this.setData({
      'exportConfig.endDate': e.detail.value
    })
  },

  /**
   * 状态筛选变化
   */
  onStatusChange(e) {
    const index = e.detail.value
    this.setData({
      statusIndex: index,
      'exportConfig.status': this.data.statusOptions[index].value
    })
  },

  /**
   * 快捷选择：最近7天
   */
  selectLast7Days() {
    const today = this.formatDate(new Date())
    const sevenDaysAgo = this.formatDate(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000))
    this.setData({
      'exportConfig.startDate': sevenDaysAgo,
      'exportConfig.endDate': today
    })
  },

  /**
   * 快捷选择：最近30天
   */
  selectLast30Days() {
    const today = this.formatDate(new Date())
    const thirtyDaysAgo = this.formatDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000))
    this.setData({
      'exportConfig.startDate': thirtyDaysAgo,
      'exportConfig.endDate': today
    })
  },

  /**
   * 快捷选择：本月
   */
  selectThisMonth() {
    const now = new Date()
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
    const today = this.formatDate(now)
    this.setData({
      'exportConfig.startDate': this.formatDate(firstDay),
      'exportConfig.endDate': today
    })
  },

  /**
   * 执行导出
   *
   * 说明：
   * 由于微信小程序无法直接下载文件到本地，
   * 这里提供两种方案：
   * 1. 复制下载链接，用户在浏览器中打开下载
   * 2. 通过后台生成文件后发送到用户邮箱（需要额外开发）
   */
  doExport() {
    const { exportConfig } = this.data

    // 验证日期
    if (!exportConfig.startDate || !exportConfig.endDate) {
      wx.showToast({ title: '请选择日期范围', icon: 'none' })
      return
    }

    if (exportConfig.startDate > exportConfig.endDate) {
      wx.showToast({ title: '开始日期不能大于结束日期', icon: 'none' })
      return
    }

    this.setData({ exporting: true })

    // 构建下载URL
    let downloadUrl = `${app.globalData.baseUrl}/super/export/work-orders?`
    downloadUrl += `start_date=${exportConfig.startDate}`
    downloadUrl += `&end_date=${exportConfig.endDate}`
    if (exportConfig.status) {
      downloadUrl += `&status=${exportConfig.status}`
    }

    // 显示下载选项
    wx.showModal({
      title: '导出数据',
      content: '数据已准备就绪。由于小程序限制，请复制链接到浏览器下载Excel文件。',
      confirmText: '复制链接',
      cancelText: '取消',
      success: (res) => {
        if (res.confirm) {
          // 复制链接到剪贴板
          wx.setClipboardData({
            data: downloadUrl,
            success: () => {
              wx.showToast({ title: '链接已复制', icon: 'success' })
              // 记录导出历史
              this.addExportHistory()
            }
          })
        }
      },
      complete: () => {
        this.setData({ exporting: false })
      }
    })
  },

  /**
   * 添加导出历史记录
   */
  addExportHistory() {
    const { exportConfig, statusOptions, statusIndex } = this.data
    const record = {
      id: Date.now(),
      startDate: exportConfig.startDate,
      endDate: exportConfig.endDate,
      status: statusOptions[statusIndex].label,
      exportTime: new Date().toLocaleString()
    }

    const history = [record, ...this.data.exportHistory].slice(0, 5)
    this.setData({ exportHistory: history })
  },

  /**
   * 预览数据（可选功能）
   */
  previewData() {
    const { exportConfig } = this.data

    // 验证日期
    if (!exportConfig.startDate || !exportConfig.endDate) {
      wx.showToast({ title: '请选择日期范围', icon: 'none' })
      return
    }

    // 跳转到工单列表页面查看
    let url = `/pages/admin/work-orders/work-orders?`
    url += `start_date=${exportConfig.startDate}`
    url += `&end_date=${exportConfig.endDate}`
    if (exportConfig.status) {
      url += `&status=${exportConfig.status}`
    }

    wx.navigateTo({ url })
  }
})
