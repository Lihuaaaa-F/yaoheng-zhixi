import { useRef } from 'react';
import { Button } from 'antd';
import { FolderOpenOutlined } from '@ant-design/icons';

export default function FilePicker({ file, onChange, accept, disabled = false, label = '选择文件' }: {
  file: File | null; onChange: (file: File | null) => void; accept: string; disabled?: boolean; label?: string;
}) {
  const input = useRef<HTMLInputElement>(null);
  return <div className="file-picker" role="group" aria-label={label}>
    <input ref={input} type="file" hidden tabIndex={-1} accept={accept} disabled={disabled} onChange={event => {
      onChange(event.target.files?.[0] ?? null);
      event.target.value = '';
    }} />
    <Button icon={<FolderOpenOutlined />} disabled={disabled} onClick={() => input.current?.click()}>{label}</Button>
    <span title={file?.name} aria-live="polite">{file?.name ?? '尚未选择文件'}</span>
  </div>;
}
