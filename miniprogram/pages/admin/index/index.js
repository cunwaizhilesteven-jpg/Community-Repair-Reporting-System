const app = getApp();
Page({
  data: { stats: { pending: 0, today: 0, completed: 0 } },
  onLoad() { this.loadStats(); },
  onShow() { this.loadStats(); },
  loadStats() {
    app.request({ url: '/admin/statistics' }).then(res => {
      const data = res.data;
      this.setData({
        stats: {
          pending: data.by_status?.pending || 0,
          today: data.total || 0,
          completed: (data.by_status?.completed || 0) + (data.by_status?.evaluated || 0)
        }
      });
    });
  },
  goTo(e) { wx.navigateTo({ url: e.currentTarget.dataset.url }); }
});
