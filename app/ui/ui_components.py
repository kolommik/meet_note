import streamlit as st
import streamlit.components.v1 as components


def copy_button(text_to_copy: str, title: str = "Скопировать"):
    """
    Создает кнопку с помощью HTML и JavaScript.
    Копирует переданный текст в буфер обмена при нажатии.
    """
    html_code = f"""
    <div style="margin-top:10px;">
        <button onclick="copyToClipboard()" style="
            padding: 8px 16px;
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
            border-radius: 4px;">
            {title}
        </button>
    </div>
    <script>
      function copyToClipboard() {{
          // Создаем временный textarea элемент
          const textarea = document.createElement('textarea');
          textarea.value = `{text_to_copy}`;
          textarea.style.position = 'fixed';  // Предотвращаем прокрутку до элемента
          textarea.style.opacity = '0';  // Делаем элемент невидимым
          document.body.appendChild(textarea);

          try {{
              // Выделяем и копируем текст
              textarea.select();
              document.execCommand('copy');
              alert('Текст скопирован в буфер обмена!');
          }} catch (err) {{
              alert('Не удалось скопировать текст: ' + err);
          }} finally {{
              // Удаляем временный элемент
              document.body.removeChild(textarea);
          }}
      }}
    </script>
    """
    components.html(html_code, height=60)


def display_file_info(file_name: str, file_size: str):
    """
    Отображает информацию о файле в UI.

    Args:
        file_name: Имя файла
        file_size: Отформатированный размер файла
    """
    info_col1, info_col2 = st.columns(2)
    with info_col1:
        st.info(f"Файл: {file_name}")
    with info_col2:
        st.info(f"Размер: {file_size}")
