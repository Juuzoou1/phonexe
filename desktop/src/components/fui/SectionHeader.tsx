import { Barcode } from "@/components/fui/Barcode";

/** Big poster-style section header: bold Arabic title + condensed Latin code
 *  + barcode, on an accent underline — ties every screen to the poster look. */
export function SectionHeader({ title, code }: { title: string; code: string }) {
  return (
    <div className="mb-3 flex items-end justify-between gap-3 border-b border-accent/20 pb-2">
      <div className="min-w-0">
        <div className="fui-label text-accent/70">// {code}</div>
        <h2 className="truncate text-[26px] font-black leading-tight text-ftext [text-shadow:0_0_14px_rgba(79,227,224,.25)]">
          {title}
        </h2>
      </div>
      <div className="flex shrink-0 items-center gap-3">
        <span
          dir="ltr"
          className="hidden font-display text-[30px] font-extrabold uppercase leading-none text-accent/20 sm:block"
          style={{ fontStretch: "75%" }}
        >
          {code}
        </span>
        <Barcode seed={code} height={18} className="text-accent/40" />
      </div>
    </div>
  );
}
