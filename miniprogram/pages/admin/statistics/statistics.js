const app = getApp();
Page({
  data: { stats: null, loading: true },
  onLoad() { this.loadStats(); },
  loadStats() {
    this.setData({ loading: true });
    app.request({ url: '/admin/statistics' }).then(res => this.setData({ stats: res.data, loading: false }));
  }
});
