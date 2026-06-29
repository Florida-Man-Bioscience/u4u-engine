import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Pipeline Validation Study — PeptOdyssey",
  description:
    "Information about an observational research study validating the accuracy of the u4u-engine genomic analysis pipeline. Pending IRB review — not yet recruiting.",
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

function Tbd({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-block rounded bg-[#edecea] px-2 py-0.5 text-[0.85em] italic text-[#6b7280]">
      {children}
    </span>
  );
}

function Fact({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-0.5 py-2 sm:grid-cols-[max-content_1fr] sm:gap-x-5 sm:py-1.5">
      <dt className="font-semibold text-[#6b7280]">{term}</dt>
      <dd>{children}</dd>
    </div>
  );
}

function Faq({ q, children }: { q: string; children: React.ReactNode }) {
  return (
    <details className="group rounded-xl border border-[#dbd9d3] bg-white">
      <summary className="flex cursor-pointer items-center justify-between gap-3 px-5 py-4 font-semibold text-[#0d1117] [&::-webkit-details-marker]:hidden">
        {q}
        <span className="text-[#1a6b4a] transition-transform group-open:rotate-180">
          ▾
        </span>
      </summary>
      <div className="px-5 pb-4 text-[#3a3f4a]">{children}</div>
    </details>
  );
}

export default function StudyPage() {
  return (
    <div className="space-y-12">
      {/* Status banner */}
      <div
        role="status"
        className="-mx-4 flex flex-wrap items-center justify-center gap-2.5 border-y border-[#fdba74] bg-[#fff7ed] px-4 py-2.5 text-center text-sm text-[#7c2d12]"
      >
        <span className="inline-block rounded-full bg-[#fdba74] px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide text-[#7c2d12]">
          Pending IRB review
        </span>
        <span>
          This study is in protocol development and <strong>is not yet recruiting</strong>. This
          page is informational only and is not a solicitation to enroll.
        </span>
      </div>

      {/* Hero */}
      <section className="space-y-4">
        <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
          Observational research study
        </p>
        <h1 className="max-w-[18ch] text-4xl leading-tight text-[#0d1117]" style={serif}>
          Validating the accuracy of a genomic analysis pipeline
        </h1>
        <p className="max-w-[60ch] text-lg text-[#3a3f4a]">
          We are preparing a research study to measure how accurately the{" "}
          <strong>u4u-engine</strong> genomic pipeline reads and interprets genetic data — by
          comparing its outputs against established reference standards. This page explains what
          the study is, what it is <em>not</em>, and how your information would be protected.
        </p>
        <div className="flex flex-wrap gap-3 pt-2">
          <a
            href="#participate"
            className="rounded-xl border border-[#1a6b4a] bg-[#1a6b4a] px-5 py-2.5 font-semibold text-white transition-colors hover:bg-[#0f4530]"
          >
            What participation involves
          </a>
          <a
            href="#contact"
            className="rounded-xl border border-[#1a6b4a] bg-white px-5 py-2.5 font-semibold text-[#1a6b4a] transition-colors hover:bg-[#e1f3eb]"
          >
            Register your interest
          </a>
        </div>
      </section>

      {/* About */}
      <section id="about" className="space-y-5 scroll-mt-20">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          About the study
        </h2>
        <p className="text-[#3a3f4a]">
          This is a <strong>diagnostic / predictive-accuracy study</strong> — an observational
          evaluation of a software pipeline. Its purpose is purely technical: does the pipeline
          compute the correct answer when the correct answer is already known from an accepted
          reference standard? Endpoints are software-accuracy measures such as variant-call
          concordance, sensitivity, specificity, and pharmacogenomic diplotype concordance.
          Reporting follows recognized standards for accuracy and prediction-model studies
          (STARD&nbsp;2015; TRIPOD&#8209;AI / PROBAST&#8209;AI).
        </p>
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="rounded-xl border border-[#dbd9d3] bg-white p-5">
            <h3 className="mb-3 text-lg text-[#0d1117]" style={serif}>
              What this study <span className="font-bold text-[#15803d]">IS</span>
            </h3>
            <ul className="list-disc space-y-1.5 pl-5 text-[#3a3f4a]">
              <li>
                An <strong>observational</strong> evaluation of how accurately the pipeline
                interprets genomic data.
              </li>
              <li>
                A comparison of pipeline outputs against reference truth sets and expert-curated
                classifications.
              </li>
              <li>
                Designed so that participation involves{" "}
                <strong>no change to your medical care</strong>.
              </li>
            </ul>
          </div>
          <div className="rounded-xl border border-[#dbd9d3] bg-white p-5">
            <h3 className="mb-3 text-lg text-[#0d1117]" style={serif}>
              What this study is <span className="font-bold text-[#b91c1c]">NOT</span>
            </h3>
            <ul className="list-disc space-y-1.5 pl-5 text-[#3a3f4a]">
              <li>
                <strong>Not</strong> a drug or peptide trial. No investigational compound (e.g.
                BPC-157, TB-500) is administered as part of this study.
              </li>
              <li>
                <strong>Not</strong> a clinical diagnostic test. The research pipeline is{" "}
                <strong>not CLIA-certified</strong> (see{" "}
                <a className="text-[#1a6b4a] underline" href="#results">
                  Results &amp; the CLIA boundary
                </a>
                ).
              </li>
              <li>
                <strong>Not</strong> currently open for enrollment.
              </li>
            </ul>
          </div>
        </div>

        <h3 className="text-lg text-[#0d1117]" style={serif}>
          Study at a glance
        </h3>
        <dl className="divide-y divide-[#dbd9d3] rounded-xl border border-[#dbd9d3] bg-white px-5">
          <Fact term="Design">
            Observational diagnostic/predictive-accuracy study (non-interventional)
          </Fact>
          <Fact term="Sponsor">Florida Man Bioscience</Fact>
          <Fact term="IRB of record">
            <Tbd>[To be confirmed — UF HRPP / IRB-01, or a reliance IRB]</Tbd>
          </Fact>
          <Fact term="Principal Investigator">
            <Tbd>[PI name &amp; credentials — TBD]</Tbd>
          </Fact>
          <Fact term="IRB protocol number">
            <Tbd>[Assigned upon submission — TBD]</Tbd>
          </Fact>
          <Fact term="Status">
            Protocol in development · <strong>not yet recruiting</strong>
          </Fact>
        </dl>
        <p className="rounded-r-xl border-l-4 border-[#2d8f61] bg-[#e1f3eb] px-4 py-3 text-[#3a3f4a]">
          The bracketed items above are finalized when the protocol is submitted and reviewed. They
          are shown as placeholders so this page stays honest about what has and has not yet been
          decided.
        </p>
      </section>

      {/* Participation */}
      <section id="participate" className="space-y-4 scroll-mt-20">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          What participation would involve
        </h2>
        <p className="text-[#3a3f4a]">
          The exact procedures are being finalized in the study protocol and confirmed through IRB
          review. In general terms, the study evaluates pipeline accuracy using either{" "}
          <strong>already-collected, de-identified genomic data</strong> or, for some participants,
          a genome data file you provide — there is no study-administered treatment and no change to
          your care.
        </p>
        <h3 className="text-lg text-[#0d1117]" style={serif}>
          Eligibility
        </h3>
        <p className="text-[#3a3f4a]">
          Detailed eligibility criteria will be set by the approved protocol.
        </p>
        <ul className="list-disc space-y-1.5 pl-5 text-[#3a3f4a]">
          <li>
            Adults able to provide informed consent <Tbd>[criteria TBD in protocol]</Tbd>
          </li>
          <li>
            <Tbd>[Additional inclusion / exclusion criteria — TBD]</Tbd>
          </li>
        </ul>
        <h3 className="text-lg text-[#0d1117]" style={serif}>
          Time &amp; compensation
        </h3>
        <dl className="divide-y divide-[#dbd9d3] rounded-xl border border-[#dbd9d3] bg-white px-5">
          <Fact term="Time commitment">
            <Tbd>[TBD — defined in protocol]</Tbd>
          </Fact>
          <Fact term="Compensation">
            <Tbd>[TBD — defined in protocol]</Tbd>
          </Fact>
        </dl>
        <div className="rounded-r-xl border-l-4 border-[#fdba74] bg-[#fff7ed] px-4 py-3 text-[#7c2d12]">
          <strong>Participation is voluntary.</strong> Enrollment has not opened. Nothing on this
          page is a consent form or an offer to enroll. If the study is approved and you choose to
          take part, you will review and sign an IRB-approved informed consent document first.
        </div>
      </section>

      {/* Privacy */}
      <section id="privacy" className="space-y-4 scroll-mt-20">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Your privacy and your rights
        </h2>
        <p className="text-[#3a3f4a]">
          Genomic data is sensitive, and the protocol is being designed around protecting it. Key
          points the consent process will cover:
        </p>
        <ul className="list-disc space-y-2 pl-5 text-[#3a3f4a]">
          <li>
            <strong>De-identification / coding.</strong> Wherever possible the study uses
            de-identified or coded data, and investigators will not attempt to re-identify
            individuals.
          </li>
          <li>
            <strong>Re-identification risk.</strong> No de-identification is perfect for genomic
            data; the consent form will state the residual risk plainly and the safeguards in place.
          </li>
          <li>
            <strong>Data security.</strong> A data management &amp; security plan (access control,
            encryption in transit and at rest, retention, and a defined coding scheme) governs any
            identifiable data.
          </li>
          <li>
            <strong>GINA.</strong> The federal Genetic Information Nondiscrimination Act limits the
            use of genetic information by health insurers and employers. Its protections have gaps —
            notably it does <em>not</em> cover life, disability, or long-term-care insurance — and
            the consent form will explain this.
          </li>
          <li>
            <strong>Certificate of Confidentiality.</strong> An NIH Certificate of Confidentiality
            (which helps shield research data from compelled disclosure) is under consideration for
            the protocol.
          </li>
          <li>
            <strong>Withdrawal.</strong> You may decline or withdraw at any time; the consent form
            will explain any limits on withdrawing data that has already been de-identified or
            shared.
          </li>
        </ul>
      </section>

      {/* Results / CLIA */}
      <section id="results" className="space-y-4 scroll-mt-20">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Results &amp; the CLIA boundary
        </h2>
        <p className="text-[#3a3f4a]">
          The research pipeline is <strong>not CLIA-certified</strong>, which means results it
          generates <strong>cannot be returned to you for clinical or medical decision-making</strong>
          . The protocol will take one of two clearly-defined approaches, decided at IRB review:
        </p>
        <ul className="list-disc space-y-1.5 pl-5 text-[#3a3f4a]">
          <li>
            <strong>Return nothing</strong> — an analysis-only study where no individual results are
            returned, or
          </li>
          <li>
            <strong>Confirm first</strong> — any potentially actionable finding is re-tested in a
            CLIA-certified laboratory before it is shared, accompanied by appropriate genetic
            counseling.
          </li>
        </ul>
        <p className="text-[#3a3f4a]">
          Either way, you should not expect to receive personal medical results from the research
          pipeline itself.
        </p>
      </section>

      {/* COI */}
      <section id="coi" className="space-y-4 scroll-mt-20">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Conflict of interest — stated up front
        </h2>
        <div className="space-y-3 rounded-r-xl border-l-4 border-[#2d8f61] bg-[#e1f3eb] px-4 py-4 text-[#3a3f4a]">
          <p>
            In the interest of transparency: the technology being evaluated in this study is the
            subject of a <strong>UF Innovate patent disclosure</strong> associated with the study
            investigator(s). An investigator who has an intellectual or financial interest in the
            technology under study is a recognized conflict of interest.
          </p>
          <p>
            This conflict is disclosed to the institutional COI committee and the IRB and is managed
            under a written conflict-of-interest management plan (including independent oversight of
            data analysis and disclosure in the consent form and any publications). It is named here
            for the same reason it will appear in the consent document — so participants know about
            it before deciding to take part.
          </p>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="space-y-3 scroll-mt-20">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Frequently asked questions
        </h2>
        <Faq q="Can I sign up now?">
          Not yet. The study is still in protocol development and IRB review, so enrollment has not
          opened. You can{" "}
          <a className="text-[#1a6b4a] underline" href="#contact">
            register your interest
          </a>{" "}
          to be notified if and when recruitment begins, with no obligation.
        </Faq>
        <Faq q="Will I be given any medicine or peptide?">
          No. This is an observational study of software accuracy. No investigational drug or peptide
          is administered as part of it. A separate, much larger type of study (an interventional
          clinical trial) would be required to test a compound — that is not what this is.
        </Faq>
        <Faq q="Will I get my genetic results back?">
          You should not expect personal medical results from the research pipeline, because it is
          not CLIA-certified. See{" "}
          <a className="text-[#1a6b4a] underline" href="#results">
            Results &amp; the CLIA boundary
          </a>{" "}
          for the two approaches the protocol may take.
        </Faq>
        <Faq q="How is my genetic data protected?">
          The study is designed to use de-identified or coded data wherever possible, under a data
          security plan with access controls and encryption. Your rights, the residual
          re-identification risk, and GINA protections (and their gaps) are detailed under{" "}
          <a className="text-[#1a6b4a] underline" href="#privacy">
            Your privacy and your rights
          </a>{" "}
          and will be covered in the informed consent process.
        </Faq>
        <Faq q="Who is running and overseeing this study?">
          The study is sponsored by Florida Man Bioscience and will be conducted under an
          Institutional Review Board (IRB) that independently reviews the protocol to protect
          participants. The IRB of record, the principal investigator, and the protocol number are
          confirmed at submission and will be listed on this page once assigned.
        </Faq>
      </section>

      {/* Contact */}
      <section id="contact" className="space-y-4 scroll-mt-20">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Register your interest / contact us
        </h2>
        <p className="text-[#3a3f4a]">
          Recruitment has not opened. If you would like to be notified if the study begins enrolling,
          or you have questions, use the contact below. Sharing your interest places you under{" "}
          <strong>no obligation</strong> and is not enrollment.
        </p>
        <dl className="divide-y divide-[#dbd9d3] rounded-xl border border-[#dbd9d3] bg-white px-5">
          <Fact term="Study team email">
            <Tbd>[study-team@ — TBD]</Tbd>
          </Fact>
          <Fact term="Principal Investigator">
            <Tbd>[PI name — TBD]</Tbd>
          </Fact>
          <Fact term="IRB contact">
            <Tbd>[IRB office contact — provided on the approved consent form]</Tbd>
          </Fact>
        </dl>
        <p className="rounded-r-xl border-l-4 border-[#2d8f61] bg-[#e1f3eb] px-4 py-3 text-[#3a3f4a]">
          Please do not send genetic data, medical records, or other sensitive personal information
          by email. The secure intake process is established as part of the approved protocol.
        </p>
      </section>

      {/* Footer / disclaimer */}
      <footer className="space-y-3 border-t border-[#dbd9d3] pt-6 text-sm text-[#6b7280]">
        <p className="rounded-xl border border-[#dbd9d3] bg-[#edecea] px-4 py-4 text-[0.82rem]">
          <strong>Disclaimer.</strong> This page is for general information about a research study
          that is in development and <strong>has not yet been approved by an IRB or opened for
          enrollment</strong>. It is not medical advice, not a diagnostic service, and not an offer
          to participate in research. Study details (design, eligibility, procedures, compensation,
          investigators, and IRB information) are not final and may change during IRB review;
          bracketed [TBD] items are confirmed at that time. If and when the study is approved,
          participation will require review and signature of an IRB-approved informed consent
          document. The research pipeline is not CLIA-certified and does not provide clinical
          results.
        </p>
        <p>
          For the internal development hub (tiers, regulatory pathway, live status), see{" "}
          <Link className="text-[#1a6b4a] underline" href="/study/dev">
            the study development hub
          </Link>
          .
        </p>
        <p>© Florida Man Bioscience. Informational draft — pending IRB review.</p>
      </footer>
    </div>
  );
}
