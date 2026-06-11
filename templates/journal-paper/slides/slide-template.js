/**
 * 单页幻灯片模板。在 compile.js 中 require 使用。
 *
 * 用法:
 *   const { createContentSlide } = require('./slide-template');
 *   const slide = createContentSlide(pptx, '标题', '内容');
 */
const COLORS = {
  primary: "2B5797",
  text: "333333",
};

/**
 * 创建内容页
 * @param {object} pptx - pptxgenjs 实例
 * @param {string} title - 标题
 * @param {string} content - 内容
 * @param {object} [opts] - 可选参数
 */
function createContentSlide(pptx, title, content, opts = {}) {
  const slide = pptx.addSlide();
  slide.addText(title, {
    x: 0.5, y: 0.3, w: 9, h: 0.8,
    fontSize: 22, color: COLORS.primary, bold: true,
  });
  slide.addText(content, {
    x: 0.8, y: 1.3, w: 8.4, h: opts.contentHeight || 5,
    fontSize: opts.fontSize || 16, color: COLORS.text,
    valign: "top", lineSpacing: opts.lineSpacing || 28,
  });
  return slide;
}

/**
 * 创建双栏内容页
 */
function createTwoColumnSlide(pptx, title, leftContent, rightContent) {
  const slide = pptx.addSlide();
  slide.addText(title, {
    x: 0.5, y: 0.3, w: 9, h: 0.8,
    fontSize: 22, color: COLORS.primary, bold: true,
  });
  slide.addText(leftContent, {
    x: 0.5, y: 1.3, w: 4.3, h: 5,
    fontSize: 14, color: COLORS.text, valign: "top",
  });
  slide.addText(rightContent, {
    x: 5.2, y: 1.3, w: 4.3, h: 5,
    fontSize: 14, color: COLORS.text, valign: "top",
  });
  return slide;
}

module.exports = { createContentSlide, createTwoColumnSlide };
