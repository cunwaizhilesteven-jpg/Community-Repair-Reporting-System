const app = getApp();
Page({
  data: { orderId: null, order: null, repairmen: [], selectedRepairman: -1, loading: true },
  onLoad(options) { this.setData({ orderId: options.id }); this.loadData(); },
  loadData() { Promise.all([this.loadDetail(), this.loadRepairmen()]); },
  loadDetail() {
    return app.request({ url: `/work-orders/${this.data.orderId}` })
      .then(res => this.setData({ order: res.data, loading: false }));
  },
  loadRepairmen() { return app.request({ url: '/admin/repairmen' }).then(res => this.setData({ repairmen: res.data })); },
  onRepairmanChange(e) { this.setData({ selectedRepairman: e.detail.value }); },
  assignOrder() {
    const idx = this.data.selectedRepairman;
    if (idx < 0) { wx.showToast({ title: '请选择维修人员', icon: 'none' }); return; }
    app.request({
      url: `/admin/work-orders/${this.data.orderId}/assign`, method: 'PUT',
      data: { repairman_id: this.data.repairmen[idx].id }
    }).then(() => { wx.showToast({ title: '分配成功' }); this.loadDetail(); });
  }
});
