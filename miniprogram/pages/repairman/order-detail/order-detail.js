const app = getApp();
Page({
  data: { orderId: null, order: null, loading: true },
  onLoad(options) { this.setData({ orderId: options.id }); this.loadDetail(); },
  onPullDownRefresh() { this.loadDetail().finally(() => wx.stopPullDownRefresh()); },
  loadDetail() {
    this.setData({ loading: true });
    return app.request({ url: `/work-orders/${this.data.orderId}` })
      .then(res => { 
        this.setData({ order: res.data, loading: false });
        app.subscribeMessages();
      })
      .catch(() => this.setData({ loading: false }));
  },
  callPhone() { wx.makePhoneCall({ phoneNumber: this.data.order.contact_phone }); },
  startOrder() {
    app.request({ url: `/repairman/work-orders/${this.data.orderId}/start`, method: 'PUT' })
      .then(() => { wx.showToast({ title: '已开始处理' }); this.loadDetail(); });
  },
  goToComplete() { wx.navigateTo({ url: `/pages/repairman/complete/complete?id=${this.data.orderId}` }); }
});
