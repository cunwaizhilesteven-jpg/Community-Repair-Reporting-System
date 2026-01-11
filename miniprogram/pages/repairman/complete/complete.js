const app = getApp();
Page({
  data: { orderId: null, remark: '', images: [], submitting: false },
  onLoad(options) { this.setData({ orderId: options.id }); },
  onRemarkInput(e) { this.setData({ remark: e.detail.value }); },
  chooseImage() {
    wx.chooseMedia({ count: 3 - this.data.images.length, mediaType: ['image'], success: res => {
      res.tempFiles.forEach(f => this.uploadImage(f.tempFilePath));
    }});
  },
  uploadImage(filePath) {
    wx.uploadFile({
      url: app.globalData.baseUrl + '/upload/image', filePath, name: 'file',
      header: { 'Authorization': `Bearer ${app.globalData.token}` },
      success: res => {
        const data = JSON.parse(res.data);
        if (data.code === 200) this.setData({ images: [...this.data.images, data.data.url] });
      }
    });
  },
  deleteImage(e) { const imgs = this.data.images; imgs.splice(e.currentTarget.dataset.index, 1); this.setData({ images: imgs }); },
  submit() {
    this.setData({ submitting: true });
    app.request({
      url: `/repairman/work-orders/${this.data.orderId}/complete`, method: 'PUT',
      data: { remark: this.data.remark, images: this.data.images }
    }).then(() => { wx.showToast({ title: '已完成' }); setTimeout(() => wx.navigateBack({ delta: 2 }), 1500); })
      .finally(() => this.setData({ submitting: false }));
  }
});
