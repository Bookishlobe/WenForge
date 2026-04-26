import { useCallback, useEffect } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import Placeholder from '@tiptap/extension-placeholder'

interface Props {
  content: string
  chapterName: string
  onSave: (content: string) => void
}

export function Editor({ content, chapterName, onSave }: Props) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Underline,
      Placeholder.configure({
        placeholder: '开始写作...',
      }),
    ],
    content: content || '<p></p>',
    onUpdate: () => {
      // Auto-save could go here with debounce
    },
    editorProps: {
      attributes: {
        class: 'prose prose-invert prose-lg max-w-none',
        style: 'min-height: 500px; outline: none;',
      },
    },
  })

  // Update editor content when switching chapters
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content || '<p></p>', false)
    }
  }, [content, chapterName])

  const handleSave = useCallback(() => {
    if (editor) {
      const text = editor.getText()
      onSave(text)
    }
  }, [editor, onSave])

  // Auto-save on Ctrl+S
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault()
        handleSave()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [handleSave])

  if (!editor) {
    return <div className="editor-placeholder">加载编辑器...</div>
  }

  return (
    <div className="editor-wrapper">
      <div className="editor-toolbar">
        <button
          onClick={() => editor.chain().focus().toggleBold().run()}
          className={editor.isActive('bold') ? 'active' : ''}
          title="粗体"
        ><strong>B</strong></button>
        <button
          onClick={() => editor.chain().focus().toggleItalic().run()}
          className={editor.isActive('italic') ? 'active' : ''}
          title="斜体"
        ><em>I</em></button>
        <button
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          className={editor.isActive('underline') ? 'active' : ''}
          title="下划线"
        ><u>U</u></button>
        <div className="separator" />
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
          className={editor.isActive('heading', { level: 1 }) ? 'active' : ''}
          title="标题1"
        >H1</button>
        <button
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
          className={editor.isActive('heading', { level: 2 }) ? 'active' : ''}
          title="标题2"
        >H2</button>
        <div className="separator" />
        <button
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          className={editor.isActive('bulletList') ? 'active' : ''}
          title="无序列表"
        >≡</button>
        <button
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          className={editor.isActive('orderedList') ? 'active' : ''}
          title="有序列表"
        >1.</button>
        <button className="save-btn" onClick={handleSave}>
          💾 保存
        </button>
      </div>

      <div className="editor-content">
        <EditorContent editor={editor} />
      </div>
    </div>
  )
}
