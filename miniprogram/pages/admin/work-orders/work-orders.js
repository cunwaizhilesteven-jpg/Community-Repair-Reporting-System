const app = getApp();
Page({
  data: { orders: [], repairmen: [], loading: true, currentStatus: 'pending' },
  onLoad() { this.loadData(); },
  onShow() { this.loadOrders(); },
  loadData() { Promise.all([this.loadOrders(), this.loadRepairmen()]); },
  loadOrders() {
    this.setData({ loading: true });
    return app.request({ url: '/admin/work-orders', data: { status: this.data.currentStatus } })
      .then(res => this.setData({ orders: res.data.items, loading: false }));
  },
  loadRepairmen() { return app.request({ url: '/admin/repairmen' }).then(res => this.setData({ repairmen: res.data })); },
  onStatusChange(e) { this.setData({ currentStatus: e.currentTarget.dataset.status }); this.loadOrders(); },
  goToDetail(e) { wx.navigateTo({ url: `/pages/admin/order-detail/order-detail?id=${e.currentTarget.dataset.id}` }); }
});
