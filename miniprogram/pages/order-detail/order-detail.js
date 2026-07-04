/**
 * 工单详情页面
 * ============
 * 显示工单的完整信息和进度时间线。
 */

const app = getApp();

Page({
  data: {
    orderId: null,
    order: null,
    loading: true
  },

  onLoad(options) {
    this.setData({ orderId: options.id });
    this.loadOrderDetail();
  },

  onPullDownRefresh() {
    this.loadOrderDetail().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  /**
   * 加载工单详情
   */
  loadOrderDetail() {
    this.setData({ loading: true });

    return app.request({
      url: `/work-orders/${this.data.orderId}`
    }).then((res) => {
      this.setData({
        order: res.data,
        loading: false
      });
      // 加载完成后请求订阅消息
      app.subscribeMessages();
    }).catch(() => {
      this.setData({ loading: false });
    });
  },

  /**
   * 预览图片
   */
  previewImage(e) {
    const { urls, current } = e.currentTarget.dataset;
    wx.previewImage({
      urls: urls,
      current: current
    });
  },

  /**
   * 拨打电话
   */
  callPhone() {
    wx.makePhoneCall({
      phoneNumber: this.data.order.contact_phone
    });
  },

  /**
   * 跳转到评价页面
   */
  goToEvaluate() {
    wx.navigateTo({
      url: `/pages/evaluate/evaluate?id=${this.data.orderId}`
    });
  }
});
