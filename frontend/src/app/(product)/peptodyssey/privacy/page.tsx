import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "PeptOdyssey Privacy Policy — Florida Man Bioscience",
  description:
    "Privacy policy for the PeptOdyssey iOS research app: HealthKit data types, purpose, retention, deletion, and contact.",
  alternates: {
    canonical: "https://peptodyssey.flmanbiosci.net/privacy",
  },
};

const serif = { fontFamily: "'DM Serif Display', serif" } as const;

export default function PeptodysseyPrivacyPage() {
  return (
    <article className="mx-auto max-w-3xl space-y-6 pb-16">
      <p className="text-xs font-bold uppercase tracking-[0.12em] text-[#1a6b4a]">
        PeptOdyssey · iOS research app
      </p>
      <h1 className="text-4xl leading-tight text-[#0d1117]" style={serif}>
        Privacy Policy
      </h1>
      <p className="font-mono text-sm text-[#6b7280]">
        Last updated: 16 July 2026 · Version 1
      </p>

      <aside
        role="note"
        className="rounded-lg border border-[#dbd9d3] border-l-4 border-l-[#92550a] bg-[#f5f4f0] px-4 py-3 text-sm text-[#3a3f4a]"
      >
        <strong className="text-[#0d1117]">Counsel review open.</strong> This
        policy is an operational draft for TestFlight and App Store disclosure.
        It is <em>not</em> legal advice. Outside counsel review remains an open
        obligation before broad external distribution or regulated study use.
        IRB / informed-consent documents, where required for a formal study, are
        separate.
      </aside>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Who we are
        </h2>
        <p>
          PeptOdyssey (“the app”) is operated by{" "}
          <strong className="text-[#0d1117]">Florida Man Bioscience</strong>{" "}
          (“we”, “us”). Contact for privacy and data requests:{" "}
          <a className="text-[#1a6b4a] underline" href="mailto:noahtjones@gmail.com">
            noahtjones@gmail.com
          </a>
          .
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          What this app does
        </h2>
        <p>
          PeptOdyssey collects health and activity data from Apple Health
          (HealthKit), with your permission, and uploads it to our research
          backend so we can study longitudinal biomarkers and run a research /
          product measurement loop for peptide-related programs. The app is a
          data-collection tool for consented participants. It is not a medical
          device and does not diagnose, treat, cure, or prevent any disease.
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          What we collect
        </h2>
        <p>
          With your explicit Health permission, the app may read a broad range
          of HealthKit data types (only those you grant in the system permission
          sheet), including:
        </p>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong className="text-[#0d1117]">Activity &amp; fitness</strong> —
            steps, distance, energy, workouts, exercise/stand/move time, VO
            <sub>2</sub> max, mobility and cycling metrics
          </li>
          <li>
            <strong className="text-[#0d1117]">Heart &amp; vitals</strong> —
            heart rate, HRV, blood pressure, respiratory rate, oxygen
            saturation, body temperature, blood glucose, related events
          </li>
          <li>
            <strong className="text-[#0d1117]">Sleep &amp; mindfulness</strong> —
            sleep analysis, mindful sessions, sleep-related vitals where
            available
          </li>
          <li>
            <strong className="text-[#0d1117]">Nutrition</strong> — energy,
            macronutrients, vitamins, minerals, water, caffeine
          </li>
          <li>
            <strong className="text-[#0d1117]">
              Body measurements &amp; characteristics
            </strong>{" "}
            — height, weight, body composition; biological sex, date of birth,
            blood type, and similar characteristics where recorded
          </li>
          <li>
            <strong className="text-[#0d1117]">
              Reproductive health &amp; symptoms
            </strong>{" "}
            — category data you have logged in Health
          </li>
          <li>
            <strong className="text-[#0d1117]">Other logged Health samples</strong>{" "}
            — e.g. audio exposure, UV, inhaler usage, hygiene events, vision
            prescription (per-object authorization)
          </li>
        </ul>
        <p>
          Clinical medical records and very high-volume series such as full ECG
          waveforms are not in the v1 collection set.
        </p>
        <p>
          We also process limited technical metadata on each sample (source app,
          device name, timestamps) and an account / subject identifier tied to
          enrollment (device token / subject id used to associate uploads).
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          How it is collected
        </h2>
        <p>
          Collection is continuous and may run in the background using Apple’s
          HealthKit background delivery so data stays current. New and updated
          samples are queued on-device and uploaded over HTTPS/TLS to our
          backend, authenticated with a per-device enrollment token. Nothing is
          read from HealthKit until you accept the in-app consent screen and
          grant Health access.
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Legal basis &amp; consent
        </h2>
        <p>
          We collect and process this data only after you provide informed
          consent in the app. You may withdraw consent at any time (see Your
          choices).
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          How we use it
        </h2>
        <p>
          We use your health data solely for the research and product-measurement
          purpose described above and to operate the app (enrollment, upload,
          sync status).{" "}
          <strong className="text-[#0d1117]">We do not sell your data.</strong>{" "}
          We do not use it for advertising or for tracking you across other
          companies’ apps or websites.
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Storage, security, and retention
        </h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            Data is stored in a PostgreSQL database on our research backend
            (reachable via{" "}
            <code className="rounded bg-[#edecea] px-1.5 py-0.5 font-mono text-[0.9em]">
              https://peptodyssey.flmanbiosci.net/api/v1
            </code>
            ).
          </li>
          <li>
            <strong className="text-[#0d1117]">In transit:</strong> encrypted via
            HTTPS/TLS.
          </li>
          <li>
            <strong className="text-[#0d1117]">At rest:</strong> hosted on
            infrastructure with disk / volume encryption as provided by the
            managed host; access restricted to authorized study and engineering
            personnel.
          </li>
          <li>
            <strong className="text-[#0d1117]">Retention:</strong> for the
            duration of active research participation and up to three (3) years
            afterward for analysis continuity, unless you request earlier
            deletion or a study protocol requires a different period. We may
            retain de-identified aggregates longer.
          </li>
        </ul>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Sharing
        </h2>
        <p>
          We share data only with service providers needed to run the study and
          backend (e.g. cloud hosting), under appropriate access controls. We do
          not sell or rent your data. We may disclose information if required by
          law.
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Your choices
        </h2>
        <ul className="list-disc space-y-2 pl-5">
          <li>
            <strong className="text-[#0d1117]">Withdraw consent</strong> in the
            app (Privacy &amp; Consent → Withdraw Consent). This stops future
            collection.
          </li>
          <li>
            <strong className="text-[#0d1117]">Revoke Health access</strong> any
            time in iOS Settings → Health → Data Access &amp; Devices →
            PeptOdyssey.
          </li>
          <li>
            <strong className="text-[#0d1117]">Request deletion</strong> of
            previously uploaded data by emailing{" "}
            <a className="text-[#1a6b4a] underline" href="mailto:noahtjones@gmail.com">
              noahtjones@gmail.com
            </a>{" "}
            with identifiers that let us locate your records.
          </li>
        </ul>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Children
        </h2>
        <p>
          PeptOdyssey is not intended for anyone under 18. We do not knowingly
          collect data from children under 18.
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Changes
        </h2>
        <p>
          We will update this policy and the in-app consent materials when
          practices change. Material changes will be reflected by a new “Last
          updated” date on this page and, where appropriate, an updated consent
          gate in the app.
        </p>
      </section>

      <section className="space-y-3 text-[#3a3f4a]">
        <h2 className="text-2xl text-[#0d1117]" style={serif}>
          Contact
        </h2>
        <p>
          Questions or data requests:{" "}
          <a className="text-[#1a6b4a] underline" href="mailto:noahtjones@gmail.com">
            noahtjones@gmail.com
          </a>
          <br />
          Florida Man Bioscience · flmanbiosci.net
        </p>
      </section>
    </article>
  );
}
