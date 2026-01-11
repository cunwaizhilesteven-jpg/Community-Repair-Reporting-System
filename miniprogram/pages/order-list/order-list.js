/**
 * 工单列表页面
 * ============
 * 显示居民的所有报修工单，支持按状态筛选。
 */

const app = getApp();

Page({
  data: {
    orders: [],           // 工单列表
    loading: true,        // 加载中
    currentStatus: '',    // 当前筛选状态
    page: 1,              // 当前页码
    hasMore: true,        // 是否有更多数据

    // 状态筛选选项
    statusOptions: [
      { value: '', label: '全部' },
      { value: 'pending', label: '待审核' },
      { value: 'assigned', label: '已分配' },
      { value: 'processing', label: '处理中' },
      { value: 'completed', label: '已完成' },
      { value: 'evaluated', label: '已评价' }
    ]
  },

  onLoad() {
    this.loadOrders();
  },

  onShow() {
    // 每次显示页面时刷新数据
    this.setData({ page: 1, orders: [] });
    this.loadOrders();
  },

  onPullDownRefresh() {
    this.setData({ page: 1, orders: [] });
    this.loadOrders().finally(() => {
      wx.stopPullDownRefresh();
    });
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadOrders();
    }
  },

  /**
   * 加载工单列表
   */
  loadOrders() {
    this.setData({ loading: true });

    return app.request({
      url: '/work-orders/mine',
      data: {
        status: this.data.currentStatus,
        page: this.data.page,
        per_page: 10
      }
    }).then((res) => {
      const newOrders = this.data.page === 1 ? res.data.items : [...this.data.orders, ...res.data.items];

      this.setData({
        orders: newOrders,
        hasMore: res.data.page < res.data.pages,
        page: this.data.page + 1,
        loading: false
      });
    }).catch(() => {
      this.setData({ loading: false });
    });
  },

  /**
   * 切换状态筛选
   */
  onStatusChange(e) {
    const status = e.currentTarget.dataset.status;
    this.setData({
      currentStatus: status,
      page: 1,
      orders: []
    });
    this.loadOrders();
  },

  /**
   * 跳转到工单详情
   */
  goToDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({
      url: `/pages/order-detail/order-detail?id=${id}`
    });
  },

  /**
   * 跳转到报修页面
   */
  goToCreate() {
    wx.navigateTo({
      url: '/pages/create-order/create-order'
    });
  }
});
