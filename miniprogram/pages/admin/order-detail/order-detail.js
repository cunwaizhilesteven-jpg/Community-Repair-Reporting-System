const app = getApp();
Page({
  data: {
    orderId: null,
    order: null,
    repairmen: [],
    selectedRepairman: -1,
    loading: true,
    // 弹窗相关
    showModal: false,
    statusOptions: [],
    selectedStatus: -1,
    statusRemark: '',
    submitting: false
  },
  onLoad(options) { this.setData({ orderId: options.id }); this.loadData(); },
  onPullDownRefresh() { this.loadDetail().finally(() => wx.stopPullDownRefresh()); },
  loadData() { Promise.all([this.loadDetail(), this.loadRepairmen()]); },
  loadDetail() {
    this.setData({ loading: true });
    return app.request({ url: '/work-orders/' + this.data.orderId })
      .then(res => this.setData({ order: res.data, loading: false }))
      .catch(() => this.setData({ loading: false }));
  },
  loadRepairmen() { return app.request({ url: '/admin/repairmen' }).then(res => this.setData({ repairmen: res.data })); },
  onRepairmanChange(e) { this.setData({ selectedRepairman: e.detail.value }); },
  assignOrder() {
    const idx = this.data.selectedRepairman;
    if (idx < 0) { wx.showToast({ title: '请选择维修人员', icon: 'none' }); return; }
    app.request({
      url: '/admin/work-orders/' + this.data.orderId + '/assign', method: 'PUT',
      data: { repairman_id: this.data.repairmen[idx].id }
    }).then(() => { wx.showToast({ title: '分配成功' }); this.loadDetail(); });
  },

  // ==========================================
  // 状态提交弹窗
  // ==========================================

  showStatusModal() {
    const statusMap = {
      'pending': '待审核',
      'assigned': '已分配',
      'processing': '处理中',
      'completed': '已完成'
    };
    const currentStatus = this.data.order.status;
    const options = Object.entries(statusMap)
      .filter(([key]) => key !== currentStatus)
      .map(([value, name]) => ({ value, name }));
    this.setData({
      showModal: true,
      statusOptions: options,
      selectedStatus: -1,
      statusRemark: ''
    });
  },

  hideStatusModal() {
    this.setData({ showModal: false });
  },

  onStatusOptionChange(e) {
    this.setData({ selectedStatus: e.detail.value });
  },

  onStatusRemarkInput(e) {
    this.setData({ statusRemark: e.detail.value });
  },

  submitStatusUpdate() {
    const { selectedStatus, statusOptions, orderId, statusRemark } = this.data;
    if (selectedStatus < 0) {
      wx.showToast({ title: '请选择目标状态', icon: 'none' });
      return;
    }
    this.setData({ submitting: true });
    app.request({
      url: '/admin/work-orders/' + orderId + '/status',
      method: 'PUT',
      data: {
        status: statusOptions[selectedStatus].value,
        remark: statusRemark
      }
    }).then(res => {
      wx.showToast({ title: '状态更新成功' });
      this.setData({
        showModal: false,
        order: res.data,
        submitting: false
      });
    }).catch(() => {
      this.setData({ submitting: false });
    });
  }
});
