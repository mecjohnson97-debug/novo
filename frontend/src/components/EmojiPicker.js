import React, { useState } from 'react';
import { Smile } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';

const EMOJIS = '😀 😃 😄 😁 😊 🙂 😉 😍 🥰 😘 😎 🤗 🤩 🥳 😇 🙏 👍 👏 🙌 💪 🤝 👋 ✌️ 👌 ❤️ 🧡 💛 💚 💙 💜 🤍 💖 ✨ 🌟 ⭐ 🔥 🎉 🎁 🌍 🌈 ☀️ 🌻 🌸 🍀 🏠 🍽️ 🍞 🥖 ☕ 👕 🧥 👟 💼 📚 🏥 💊 ⚖️ 🚗 🚌 📍 📞 💬 ✅ ❗ ❓ 😢 😔 😅 🤔 😮 🙈'.split(' ');

export default function EmojiPicker({ onPick, testId = 'emoji-picker-button', className = '' }) {
  const [open, setOpen] = useState(false);
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button type="button" aria-label="Emojis" data-testid={testId}
          className={`grid h-9 w-9 flex-shrink-0 place-items-center rounded-full text-[#8C827A] transition-colors hover:bg-[#F1EBE1] hover:text-[#C8894F] ${className}`}>
          <Smile size={20} />
        </button>
      </PopoverTrigger>
      <PopoverContent className="notranslate w-72 p-2" align="start" data-testid="emoji-picker-panel">
        <div className="grid grid-cols-9 gap-0.5">
          {EMOJIS.map((e) => (
            <button key={e} type="button" onClick={() => onPick(e)} className="rounded-md p-1 text-xl leading-none hover:bg-[#F1EBE1]" data-testid={`emoji-${e}`}>{e}</button>
          ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}
