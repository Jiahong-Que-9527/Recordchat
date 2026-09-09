import Image from "next/image";
import { cn } from "@/lib/utils";

const SIZES = {
  sm: { className: "h-7 w-7 rounded-lg", px: 28 },
  md: { className: "h-8 w-8 rounded-xl", px: 32 },
  lg: { className: "h-14 w-14 rounded-2xl", px: 56 },
  xl: { className: "h-20 w-20 rounded-[1.35rem]", px: 80 },
  hero: { className: "h-24 w-24 rounded-[1.5rem]", px: 96 },
} as const;

export function RecordChatIcon({
  size = "sm",
  className,
  priority = false,
  animated = false,
  alt = "",
}: {
  size?: keyof typeof SIZES;
  className?: string;
  priority?: boolean;
  animated?: boolean;
  alt?: string;
}) {
  const { className: sizeClass, px } = SIZES[size];

  return (
    <Image
      src="/recordchat-icon.png"
      alt={alt}
      width={px}
      height={px}
      priority={priority}
      className={cn(
        sizeClass,
        "shrink-0 shadow-rc-icon",
        animated && "animate-rc-float",
        className
      )}
    />
  );
}
