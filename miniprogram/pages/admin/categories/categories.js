const app = getApp();
Page({
  data: { categories: [], loading: true },
  onLoad() { this.loadCategories(); },
  onShow() { this.loadCategories(); },
  loadCategories() {
    this.setData({ loading: true });
    app.request({ url: '/categories' }).then(res => this.setData({ categories: res.data, loading: false }));
  },
  addCategory() {
    wx.showModal({
      title: '添加类别', editable: true, placeholderText: '请输入类别名称',
      success: res => {
        if (res.confirm && res.content) {
          app.request({ url: '/admin/categories', method: 'POST', data: { name: res.content } })
            .then(() => { wx.showToast({ title: '添加成功' }); this.loadCategories(); });
        }
      }
    });
  },
  deleteCategory(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({ title: '确认删除', content: '确定要删除此类别吗？', success: res => {
      if (res.confirm) {
        app.request({ url: `/admin/categories/${id}`, method: 'DELETE' })
          .then(() => { wx.showToast({ title: '删除成功' }); this.loadCategories(); });
      }
    }});
  }
});
