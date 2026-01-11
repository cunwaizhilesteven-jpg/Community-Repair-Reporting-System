/**
 * 评价页面
 * ========
 * 居民对维修服务进行评价。
 */

const app = getApp();

Page({
  data: {
    orderId: null,
    rating: 5,           // 默认5星
    content: '',         // 评价内容
    submitting: false
  },

  onLoad(options) {
    this.setData({ orderId: options.id });
  },

  /**
   * 选择评分
   */
  onRatingChange(e) {
    const rating = e.currentTarget.dataset.rating;
    this.setData({ rating });
  },

  /**
   * 输入评价内容
   */
  onContentInput(e) {
    this.setData({ content: e.detail.value });
  },

  /**
   * 提交评价
   */
  submitEvaluation() {
    if (this.data.submitting) return;

    this.setData({ submitting: true });

    app.request({
      url: `/work-orders/${this.data.orderId}/evaluate`,
      method: 'POST',
      data: {
        rating: this.data.rating,
        content: this.data.content
      }
    }).then(() => {
      wx.showToast({ title: '评价成功', icon: 'success' });
      setTimeout(() => {
        wx.navigateBack();
      }, 1500);
    }).finally(() => {
      this.setData({ submitting: false });
    });
  }
});
