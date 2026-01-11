/**
 * 首页
 * ====
 * 居民进入小程序后看到的第一个页面。
 *
 * 功能：
 * 1. 快捷报修入口
 * 2. 显示最近的工单
 */

const app = getApp();

Page({
  /**
   * 页面数据
   * 这里定义的数据可以在 WXML 中使用 {{变量名}} 显示
   */
  data: {
    userInfo: null,      // 用户信息
    recentOrders: [],    // 最近工单列表
    loading: true,       // 是否正在加载
    isLoggedIn: false    // 是否已登录
  },

  /**
   * 页面加载时执行
   */
  onLoad() {
    this.checkLogin();
  },

  /**
   * 页面显示时执行（每次进入页面都会调用）
   */
  onShow() {
    if (app.globalData.isLoggedIn) {
      this.loadRecentOrders();
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadRecentOrders().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 检查登录状态
   */
  checkLogin() {
    if (app.globalData.isLoggedIn) {
      this.setData({
        userInfo: app.globalData.userInfo,
        isLoggedIn: true
      });
      this.loadRecentOrders();
    } else {
      // 自动登录
      this.handleLogin();
    }
  },

  /**
   * 处理登录
   */
  handleLogin() {
    wx.showLoading({ title: '登录中...' });

    app.login()
      .then((data) => {
        this.setData({
          userInfo: data.user,
          isLoggedIn: true
        });
        this.loadRecentOrders();
      })
      .catch((err) => {
        console.error('登录失败', err);
        this.setData({ loading: false });
      })
      .finally(() => {
        wx.hideLoading();
      });
  },

  /**
   * 加载最近工单
   */
  loadRecentOrders() {
    this.setData({ loading: true });

    return app.request({
      url: '/work-orders/mine',
      data: { per_page: 3 }  // 只显示最近3条
    })
      .then((res) => {
        this.setData({
          recentOrders: res.data.items,
          loading: false
        });
      })
      .catch(() => {
        this.setData({ loading: false });
      });
  },

  /**
   * 跳转到报修页面
   */
  goToCreateOrder() {
    wx.navigateTo({
      url: '/pages/create-order/create-order'
    });
  },

  /**
   * 跳转到工单详情
   */
  goToOrderDetail(e) {
    const orderId = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/order-detail/order-detail?id=${orderId}`
    });
  },

  /**
   * 跳转到工单列表
   */
  goToOrderList() {
    wx.switchTab({
      url: '/pages/order-list/order-list'
    });
  },

  /**
   * 根据角色跳转到对应页面
   */
  goToRolePage() {
    const role = this.data.userInfo?.role;

    if (role === 'repairman') {
      wx.navigateTo({
        url: '/pages/repairman/index/index'
      });
    } else if (role === 'admin' || role === 'super') {
      wx.navigateTo({
        url: '/pages/admin/index/index'
      });
    }
  }
});
