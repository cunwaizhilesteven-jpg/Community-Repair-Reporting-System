/**
 * 维修人员工单列表页面
 */
const app = getApp();

Page({
  data: {
    orders: [],
    loading: true,
    currentStatus: 'assigned',
    statusOptions: [
      { value: 'assigned', label: '待处理' },
      { value: 'processing', label: '处理中' },
      { value: 'completed', label: '已完成' }
    ]
  },

  onLoad() {
    this.loadOrders();
  },

  onShow() {
    this.loadOrders();
  },

  onPullDownRefresh() {
    this.loadOrders().finally(() => wx.stopPullDownRefresh());
  },

  loadOrders() {
    this.setData({ loading: true });
    return app.request({
      url: '/repairman/work-orders',
      data: { status: this.data.currentStatus }
    }).then(res => {
      this.setData({ orders: res.data.items, loading: false });
    }).catch(() => this.setData({ loading: false }));
  },

  onStatusChange(e) {
    this.setData({ currentStatus: e.currentTarget.dataset.status });
    this.loadOrders();
  },

  goToDetail(e) {
    wx.navigateTo({
      url: `/pages/repairman/order-detail/order-detail?id=${e.currentTarget.dataset.id}`
    });
  }
});
