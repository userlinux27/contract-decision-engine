import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Добавляем CSS для info-blocks
css_to_add = '''        /* New: Info blocks */
        .info-blocks {
            display: flex;
            gap: 32px;
            margin-top: 40px;
            padding-top: 32px;
            border-top: 1px solid #27272a;
            justify-content: center;
            text-align: left;
        }

        .info-block {
            flex: 1;
            max-width: 280px;
        }

        .info-block h3 {
            font-size: 0.85rem;
            font-weight: 600;
            color: #e4e4e7;
            margin-bottom: 8px;
            letter-spacing: 0.3px;
        }

        .info-block p {
            font-size: 0.8rem;
            color: #71717a;
            line-height: 1.5;
        }

        @media (max-width: 480px) {
            .info-blocks {
                flex-direction: column;
                gap: 24px;
                align-items: center;
            }
            .info-block {
                max-width: 100%;
                text-align: center;
            }
        }'''

# Находим место для добавления CSS (перед медиа-запросами)
css_insert_point = content.find('@media (max-width: 480px)')
if css_insert_point != -1:
    content = content[:css_insert_point] + css_to_add + content[css_insert_point:]

# 2. Заменяем старый footer на новый
old_footer = '''            <p style="margin-top: 28px;"><a href="/static/about.html" style="color:#6366f1;">About this service</a></p>
            <p class="footer-note">Based on detected issues. This is not legal advice.</p>
        </div>'''

new_footer = '''            <p style="margin-top: 28px;"><a href="about.html" style="color:#6366f1;">About this service</a></p>
            <p style="margin-top: 8px; font-size: 0.8rem; color: #52525b;">Questions or feedback? <a href="mailto:feedback@workmatic.pro" style="color:#6366f1;">feedback@workmatic.pro</a></p>
            <p class="footer-note">Based on detected issues. This is not legal advice.</p>
            
            <div class="info-blocks">
                <div class="info-block">
                    <h3>What we check</h3>
                    <p>We look for key contract risks such as termination terms, fees and penalties, liability, payment terms, jurisdiction, unilateral changes and other clauses that may deserve a closer look.</p>
                </div>
                <div class="info-block">
                    <h3>Privacy matters</h3>
                    <p>Your PDF is processed temporarily on our server and removed after processing. Relevant contract excerpts identified during the analysis may be sent to our external AI provider to generate explanations.</p>
                </div>
            </div>
        </div>'''

content = content.replace(old_footer, new_footer)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Все изменения внесены успешно')