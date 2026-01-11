/**
 * 超级管理员首页
 * ================
 * 系统概览和快捷入口
 *
 * 为什么需要这个页面？
 * - 提供系统整体数据概览
 * - 快捷入口方便管理操作
 */

const app = getApp()

Page({
  data: {
    // 系统概览数据
    overview: {
      totalUsers: 0,      // 总用户数
      totalBuildings: 0,  // 总楼栋数
      totalOrders: 0,     // 总工单数
      todayOrders: 0      // 今日工单
    },
    // 用户统计
    userStats: {
      residents: 0,       // 居民数
      repairmen: 0,       // 维修人员数
      admins: 0           // 管理员数
    },
    loading: true
  },

  onLoad() {
    this.loadOverview()
  },

  onShow() {
    // 每次显示时刷新数据
    this.loadOverview()
  },

  /**
   * 加载系统概览数据
   */
  loadOverview() {
    this.setData({ loading: true })

    // 并行请求多个统计接口
    Promise.all([
      this.getUserStats(),
      this.getBuildingCount(),
      this.getOrderStats()
    ]).then(() => {
      this.setData({ loading: false })
    }).catch(() => {
      this.setData({ loading: false })
    })
  },

  /**
   * 获取用户统计
   */
  getUserStats() {
    return new Promise((resolve) => {
      app.request({
        url: '/super/users?per_page=1',
        success: (res) => {
          if (res.data.code === 200) {
            this.setData({
              'overview.totalUsers': res.data.data.total
            })
          }
          resolve()
        },
        fail: () => resolve()
      })
    })
  },

  /**
   * 获取楼栋数量
   */
  getBuildingCount() {
    return new Promise((resolve) => {
      app.request({
        url: '/buildings',
        success: (res) => {
          if (res.data.code === 200) {
            this.setData({
              'overview.totalBuildings': res.data.data.length
            })
          }
          resolve()
        },
        fail: () => resolve()
      })
    })
  },

  /**
   * 获取工单统计
   */
  getOrderStats() {
    return new Promise((resolve) => {
      app.request({
        url: '/admin/statistics',
        success: (res) => {
          if (res.data.code === 200) {
            const stats = res.data.data
            this.setData({
              'overview.totalOrders': stats.total || 0,
              'overview.todayOrders': stats.today_count || 0
            })
          }
          resolve()
        },
        fail: () => resolve()
      })
    })
  },

  /**
   * 跳转到用户管理
   */
  goToUsers() {
    wx.navigateTo({
      url: '/pages/super/users/users'
    })
  },

  /**
   * 跳转到楼栋管理
   */
  goToBuildings() {
    wx.navigateTo({
      url: '/pages/super/buildings/buildings'
    })
  },

  /**
   * 跳转到数据导出
   */
  goToExport() {
    wx.navigateTo({
      url: '/pages/super/export/export'
    })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadOverview()
    wx.stopPullDownRefresh()
  }
})
