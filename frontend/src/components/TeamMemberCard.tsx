import type { TeamMember } from "@/lib/team";

type Props = {
  member: TeamMember;
  /** denser card for homepage grid */
  compact?: boolean;
};

export function TeamMemberCard({ member, compact = false }: Props) {
  const hasPhoto = Boolean(member.imgFallback || member.img);

  return (
    <article
      className={`overflow-hidden rounded-xl border border-[#dbd9d3] bg-white ${
        compact ? "" : "flex flex-col"
      }`}
    >
      {hasPhoto ? (
        <picture>
          {member.img ? (
            <source type="image/webp" srcSet={member.img} />
          ) : null}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={member.imgFallback || member.img}
            alt={`Portrait of ${member.name}`}
            width={800}
            height={800}
            className="aspect-square w-full object-cover"
            loading="lazy"
          />
        </picture>
      ) : (
        <div
          className="grid aspect-square w-full place-items-center bg-gradient-to-br from-[#1a6b4a] to-[#0f4530] text-3xl font-semibold tracking-wide text-white md:text-4xl"
          aria-hidden
        >
          {member.initials}
        </div>
      )}
      <div className={compact ? "p-4" : "flex flex-1 flex-col gap-2 p-5"}>
        <div className="font-semibold text-[#0d1117]">{member.name}</div>
        <div className="text-sm text-[#1a6b4a]">{member.role}</div>
        {!compact && member.blurb ? (
          <p className="mt-1 text-sm leading-relaxed text-[#3a3f4a]">
            {member.blurb}
          </p>
        ) : null}
        {member.nucleateActivator ? (
          <p
            className={`text-[11px] font-semibold uppercase tracking-[0.12em] text-[#6b7280] ${
              compact ? "mt-2" : "mt-auto pt-2"
            }`}
          >
            Nucleate Activator
          </p>
        ) : null}
      </div>
    </article>
  );
}
