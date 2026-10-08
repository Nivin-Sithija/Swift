from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from pypdf import PdfReader

root = Path.cwd()
out = root / 'output/pdf/Shazan_Individual_Contribution.pdf'
styles = {
 'title': ParagraphStyle('title', fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#17354A'), spaceAfter=9),
 'meta': ParagraphStyle('meta', fontName='Helvetica', fontSize=10.5, leading=14, textColor=colors.HexColor('#46535D'), spaceAfter=12),
 'section': ParagraphStyle('section', fontName='Helvetica-Bold', fontSize=11.5, leading=15, textColor=colors.HexColor('#17354A'), spaceBefore=12, spaceAfter=7),
 'bullet': ParagraphStyle('bullet', fontName='Helvetica', fontSize=10.5, leading=14.2, textColor=colors.HexColor('#20262B'), leftIndent=11, firstLineIndent=0, bulletIndent=0, spaceAfter=6),
}
contributions = [
'<b>Project planning:</b> Participated in brainstorming discussions and explored the dataset to support the project\'s initial direction.',
'<b>Multilingual dataset preparation:</b> Researched Tamil code-mixed translation methods, translated the dataset into Tamil and Tanglish, validated sentiment labels, and revised the Tamil translation strategy.',
'<b>Model development:</b> Analysed tokenizers, built a runnable TF-IDF baseline pipeline, completed the initial transformer setup, and fine-tuned the classifier while exploring suitable model options.',
'<b>OCR development:</b> Worked on initial OCR model experiments, finalised the model using augmented training images, and established an end-to-end OCR pipeline.',
'<b>OCR masking:</b> Implemented OCR masking as part of the image-processing workflow.',
'<b>Model hosting:</b> Hosted the model on Hugging Face and incorporated confidence scores into prediction outputs.',
'<b>Application improvements:</b> Contributed to backend optimisation and refined the frontend user interface.',
'<b>Testing and reporting:</b> Supported system testing, organised testing materials, and helped arrange the project report.',
'<b>Evaluation presentations:</b> Prepared the slides for both the mid-evaluation and final-evaluation presentations.',
]
challenges = [
'<b>Preserving meaning and sentiment across languages:</b> Addressed Tamil and Tanglish translation difficulties by reviewing translated text, validating sentiment labels, and revising the translation approach.',
'<b>Processing code-mixed text:</b> Addressed spelling and language-representation differences through tokenizer analysis, a TF-IDF baseline, and transformer model experimentation and fine-tuning.',
'<b>Handling variations in OCR input:</b> Used augmented training images and refined the OCR pipeline to address differences in image quality and text appearance.',
'<b>Communicating the project clearly:</b> Organised the evaluation slides and report around the project objectives, methodology, implementation, and outcomes to present the work coherently.',
]
doc = SimpleDocTemplate(str(out), pagesize=A4, rightMargin=43, leftMargin=43, topMargin=39, bottomMargin=36, title='Individual Contribution to the Project - Shazan', author='Shazan')
story = [Paragraph('Individual Contribution to the Project', styles['title']), Paragraph('<b>Shazan</b> &nbsp; | &nbsp; Student ID: 230611F', styles['meta']), HRFlowable(width='100%', thickness=0.8, color=colors.HexColor('#C5D2DC'))]
for heading, items in [('My Contributions', contributions), ('Challenges and How I Overcame Them', challenges)]:
    story.append(Paragraph(heading, styles['section']))
    story.extend(Paragraph(item, styles['bullet'], bulletText='\u2022') for item in items)
doc.build(story)
reader = PdfReader(str(out))
assert len(reader.pages) == 1, f'Expected one page, found {len(reader.pages)}'
assert '230611F' in reader.pages[0].extract_text()
print(f'Created {out}; pages: {len(reader.pages)}')
