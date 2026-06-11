/**
 * 论文答辩 PPT 生成模板。
 * 用法: node compile.js
 */
const pptxgen = require("pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_16x9";
pptx.author = "{AUTHOR}";
pptx.title = "{TITLE}";

// 主题色
const COLORS = {
  primary: "2B5797",
  secondary: "4472C4",
  text: "333333",
  light: "D6E4F0",
  white: "FFFFFF",
};

// Slide 1: 封面
let slide1 = pptx.addSlide();
slide1.addText("{TITLE}\n——{SUBTITLE}", { x: 0.8, y: 1.5, w: 8.4, h: 2.5, fontSize: 28, color: COLORS.primary, bold: true, align: "center" });
slide1.addText("{AUTHOR}  {AFFILIATION}", { x: 0.8, y: 4.2, w: 8.4, h: 0.6, fontSize: 16, color: COLORS.text, align: "center" });
slide1.addText(new Date().getFullYear() + "年", { x: 0.8, y: 5.0, w: 8.4, h: 0.5, fontSize: 14, color: COLORS.text, align: "center" });

// Slide 2: 目录
let slide2 = pptx.addSlide();
slide2.addText("汇报提纲", { x: 0.5, y: 0.3, w: 9, h: 0.8, fontSize: 24, color: COLORS.primary, bold: true });
slide2.addText("一、{SECTION_1_TITLE}\n二、{SECTION_2_TITLE}\n三、{SECTION_3_TITLE}\n四、{SECTION_4_TITLE}\n五、结论与建议", { x: 1.0, y: 1.5, w: 8, h: 4, fontSize: 18, color: COLORS.text, lineSpacing: 40 });

// Slide 3-5: 内容页（复制此模式）
for (let i = 1; i <= 3; i++) {
  let s = pptx.addSlide();
  s.addText(`{SECTION_${i}_TITLE}`, { x: 0.5, y: 0.3, w: 9, h: 0.8, fontSize: 22, color: COLORS.primary, bold: true });
  s.addText("{CONTENT_PLACEHOLDER}", { x: 0.8, y: 1.3, w: 8.4, h: 5, fontSize: 16, color: COLORS.text, valign: "top" });
}

// Slide 6: 致谢
let slideEnd = pptx.addSlide();
slideEnd.addText("谢谢各位专家！", { x: 0.8, y: 2.0, w: 8.4, h: 2, fontSize: 36, color: COLORS.primary, bold: true, align: "center" });
slideEnd.addText("敬请批评指正", { x: 0.8, y: 4.2, w: 8.4, h: 0.8, fontSize: 18, color: COLORS.text, align: "center" });

pptx.writeFile({ fileName: "配图.pptx" })
  .then(() => console.log("已生成: 配图.pptx"))
  .catch(err => console.error("生成失败:", err));
