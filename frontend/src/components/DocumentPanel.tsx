import React, { useState } from 'react';

export const DocumentPanel: React.FC = () => {
  const [dataExpanded, setDataExpanded] = useState(false);

  return (
    <article className="lg:col-span-8 flex flex-col gap-12 bg-[#0D1420]/90 backdrop-blur-2xl rounded-3xl p-10 sm:p-12 relative border border-[#3D8BFF]/15 shadow-[0_0_40px_-10px_rgba(61,139,255,0.1)]" style={{ backgroundImage: 'radial-gradient(circle at 50% 0%, rgba(61, 139, 255, 0.06) 0%, transparent 70%)' }}>
      <div className="absolute top-10 right-10 pointer-events-none opacity-15">
        <svg fill="none" height="140" viewBox="0 0 100 100" width="140">
          <polygon points="50,5 90,85 10,85" stroke="#3D8BFF" strokeWidth="1.5"></polygon>
          <line stroke="#6BA8FF" strokeWidth="1" x1="50" x2="50" y1="5" y2="85"></line>
          <circle cx="50" cy="5" fill="#6BA8FF" r="3.5"></circle>
          <circle cx="90" cy="85" fill="#3D8BFF" r="3.5"></circle>
          <circle cx="10" cy="85" fill="#3D8BFF" r="3.5"></circle>
          <circle cx="50" cy="45" fill="#6BA8FF" r="4"></circle>
        </svg>
      </div>

      <section className="bg-gradient-to-b from-surface-elevated/80 to-[#0A101A]/80 rounded-2xl p-10 relative overflow-hidden border border-[#3D8BFF]/20 shadow-[0_0_32px_-6px_rgba(61,139,255,0.12)]">
        <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-accent-glow to-primary shadow-[0_0_14px_#6BA8FF]"></div>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-accent-glow text-[24px] drop-shadow-[0_0_10px_rgba(107,168,255,0.6)]">analytics</span>
            <h2 className="font-label-md text-label-md uppercase tracking-widest text-accent-glow font-semibold">Executive Synthesis</h2>
          </div>
          <span className="font-citation text-citation text-text-muted px-3 py-1 rounded-full bg-surface-container/70 border border-[#3D8BFF]/15 tracking-wider">EVAL-METRIC-99.2</span>
        </div>
        <p className="font-body-lg text-[18px] text-text-primary/95 leading-[32px] font-light">
          Sustained extreme-rate charging (&gt;4C) across garnet-type {'$\\mathrm{Li_{6.4}La_3Zr_{1.4}Ta_{0.6}O_{12}}$'} (LLZO) electrolytes triggers catastrophic local shear stress at microscopic grain boundaries. This synthesis consolidates empirical data confirming that void coalescence and mechanical pinning at defective triple-junctions drive lithium infiltration prior to classical electrochemical short-circuiting
          <CitePill id="1" />
          <CitePill id="2" />.
        </p>
      </section>

      <section className="bg-gradient-to-b from-surface-container/50 to-[#0A101A]/60 rounded-2xl p-10 relative overflow-hidden border border-[#3D8BFF]/20 shadow-[0_0_30px_-6px_rgba(61,139,255,0.1)]">
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent-glow shadow-[0_0_12px_#6BA8FF]"></div>
        <div className="flex items-center justify-between gap-3.5 mb-7">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-accent-glow text-[26px] drop-shadow-[0_0_10px_rgba(107,168,255,0.6)]">lightbulb</span>
            <h3 className="text-2xl font-light text-text-primary tracking-tight">Key Engineering Takeaways</h3>
          </div>
          <span className="font-label-sm text-[11px] uppercase tracking-wider text-accent-glow/90 px-3 py-1 rounded-full bg-primary/10 border border-[#3D8BFF]/25">Primary Findings</span>
        </div>
        
        <ul className="space-y-6 text-secondary text-base leading-[28px] pl-1 font-light">
          <TakeawayItem 
            title="Microstructural Refinement" 
            text="Sub-micron grain sizing (<3μm) through co-dopant engineering diminishes grain boundary shear stress concentrations by up to 47%." 
          />
          <TakeawayItem 
            title="Interfacial Compliance Layer" 
            text="Incorporating a nanoscale lithiophilic buffer ($Al_2O_3$ or Sn-alloy) prevents premature void coalescing beyond 4C rates." 
          />
          <TakeawayItem 
            title="Stack Pressure Regulation" 
            text="Maintaining dynamic stack pressure (≥5.0 MPa) maintains intimate atomic contact, suppressing rapid dendritic percolation along triple junctions." 
          />
        </ul>
      </section>

      <div className="rounded-2xl border border-[#3D8BFF]/20 bg-[#090e17]/80 backdrop-blur-xl overflow-hidden transition-all duration-300">
        <button 
          onClick={() => setDataExpanded(!dataExpanded)}
          className="w-full flex items-center justify-between p-6 px-8 text-left hover:bg-surface-elevated/40 transition-colors group cursor-pointer"
        >
          <div className="flex items-center gap-3.5">
            <div className="w-8 h-8 rounded-lg bg-primary/15 border border-[#3D8BFF]/30 flex items-center justify-center text-accent-glow group-hover:shadow-[0_0_12px_rgba(61,139,255,0.4)] transition-all">
              <span className={`material-symbols-outlined text-[20px] transition-transform duration-300 ${dataExpanded ? 'rotate-180' : ''}`}>expand_more</span>
            </div>
            <div>
              <span className="font-headline-sm text-headline-sm text-text-primary group-hover:text-accent-glow transition-colors font-medium block">Supporting Data & Telemetry</span>
              <span className="font-label-sm text-[11px] text-text-muted/80 tracking-wide">Metrics grid, localized stress simulation (Fig 1.1) & CCD threshold dataset</span>
            </div>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="px-3 py-1 rounded-full bg-surface-container/80 border border-[#3D8BFF]/15 text-accent-glow font-citation text-[11px] tracking-wider uppercase font-semibold">
              {dataExpanded ? '3 modules active' : '3 modules collapsed'}
            </span>
            <span className="font-label-sm text-xs text-primary group-hover:underline hidden sm:inline">
              {dataExpanded ? 'Collapse' : 'Expand'}
            </span>
          </div>
        </button>
        
        {dataExpanded && (
          <div className="px-8 pb-8 pt-4 space-y-10 border-t border-[#3D8BFF]/15">
            <div className="pt-2">
              <div className="flex items-center justify-between mb-4">
                <h4 className="font-label-md text-label-md uppercase tracking-widest text-text-muted flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent-glow"></span>Key Empirical Metrics
                </h4>
                <span className="font-citation text-citation text-text-muted/70">Confidence: 98.4%</span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-5">
                <MetricCard title="Avg Critical CCD" value="14.2" unit="mA/cm²" subtext="+34% w/ Al-doping" subtextIcon="arrow_upward" subtextColor="text-state-success" />
                <MetricCard title="Void Nucleation" value="τ = 184s" subtext="Under 4.5C load" glow={true} />
                <MetricCard title="Fracture Toughness" value="0.92" unit="MPa·m½" subtext="High brittleness" subtextIcon="arrow_downward" subtextColor="text-state-error" />
                <MetricCard title="Confidence Level" value="98.4%" subtext="18 validated trials" isSuccess={true} />
              </div>
            </div>

            <section className="space-y-6 pt-4 border-t border-[#3D8BFF]/15">
              <div className="flex items-center gap-3.5">
                <span className="font-mono text-sm text-accent-glow font-bold px-2.5 py-1 rounded-lg bg-primary/10 border border-[#3D8BFF]/25 shadow-[0_0_12px_rgba(61,139,255,0.15)]">01</span>
                <h2 className="text-2xl font-light text-text-primary tracking-tight">Interfacial Stress Accumulation & Void Nucleation</h2>
              </div>
              <p className="text-base text-secondary leading-relaxed font-light">
                During lithium plating at high current densities exceeding the critical current threshold, electro-chemo-mechanical overpotential generates steep vacancy concentration gradients along the lithium/LLZO interface. When the local vacancy flux fails to keep pace with lithium atom extraction during continuous cycling, nanoscale voids nucleate at localized unbonded regions<CitePill id="1" />.
              </p>
              
              <div className="bg-gradient-to-b from-surface-elevated/70 to-[#0A101A]/70 rounded-2xl p-7 my-6 border border-[#3D8BFF]/15 shadow-[0_0_28px_-6px_rgba(61,139,255,0.08)] relative overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(61,139,255,0.05)_0%,transparent_70%)] pointer-events-none"></div>
                <div className="flex items-center justify-between mb-5">
                  <span className="font-label-sm text-label-sm text-text-muted uppercase tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-accent-glow shadow-[0_0_8px_#6BA8FF]"></span>
                    Fig 1.1: Localized Shear Stress (σ_eff) vs. Plating Current Density
                  </span>
                  <span className="font-citation text-citation text-text-muted font-mono">FEM Simulation (N=1,200)</span>
                </div>
                
                <div className="h-48 w-full flex items-end gap-3.5 pt-4 px-2 relative">
                  <div className="absolute inset-x-2 inset-y-4 flex flex-col justify-between pointer-events-none opacity-15">
                    <div className="w-full h-px bg-text-muted"></div>
                    <div className="w-full h-px bg-text-muted"></div>
                    <div className="w-full h-px bg-text-muted"></div>
                    <div className="w-full h-px bg-text-muted"></div>
                  </div>
                  
                  <ChartBar height="h-12" label="1C" tooltip="1.2 MPa" />
                  <ChartBar height="h-20" label="2C" tooltip="2.8 MPa" />
                  <ChartBar height="h-28" label="3C" tooltip="5.9 MPa" />
                  <ChartBar height="h-36" label="4C" tooltip="12.4 MPa • CRITICAL" variant="warning" />
                  <ChartBar height="h-44" label="5C+" tooltip="18.7 MPa • RUPTURE" variant="danger" />
                </div>
                
                <div className="flex items-center justify-between mt-5 text-text-muted font-citation text-citation pt-3.5 border-t border-[#3D8BFF]/15">
                  <span>Critical Stress Limit: 11.8 MPa (Griffith's Criterion)</span>
                  <span className="text-accent-glow font-medium drop-shadow-[0_0_8px_rgba(107,168,255,0.4)]">Defect propagation occurs at ≥4C</span>
                </div>
              </div>
              
              <p className="text-base text-secondary leading-relaxed font-light">
                These voids reduce the effective electroactive contact area, triggering current constriction into residual contact asperities. Argonne National Laboratory testing cycles<CitePill id="2" /> indicate local current focusing as high as 80× nominal values, precipitating intergranular shear fractures that permit rapid lithium whisker intrusion through polycrystalline boundaries<CitePill id="3" />.
              </p>
            </section>
            
            <section className="space-y-6 pt-4 border-t border-[#3D8BFF]/15">
              <div className="flex items-center gap-3.5">
                <span className="font-mono text-sm text-accent-glow font-bold px-2.5 py-1 rounded-lg bg-primary/10 border border-[#3D8BFF]/25 shadow-[0_0_12px_rgba(61,139,255,0.15)]">02</span>
                <h2 className="text-2xl font-light text-text-primary tracking-tight">Critical Current Density (CCD) Thresholds and Grain Boundary Chemistry</h2>
              </div>
              <p className="text-base text-secondary leading-relaxed font-light">
                Garnet grain boundaries exhibit elevated electronic conductivity relative to single crystal bulk domains, an effect significantly amplified by surface contamination such as {'$\\mathrm{Li_2CO_3}$'} or protonated moisture passivations<CitePill id="4" />. Comparative testing across varied dopant profiles yields distinct critical thresholds:
              </p>
              
              <div className="overflow-x-auto bg-surface-elevated/50 rounded-2xl border border-[#3D8BFF]/15 backdrop-blur-sm shadow-[0_0_24px_-6px_rgba(61,139,255,0.08)]">
                <table className="w-full text-left font-body-sm text-body-sm">
                  <thead>
                    <tr className="bg-surface-container/60 font-label-sm text-[11px] text-text-muted uppercase tracking-widest border-b border-[#3D8BFF]/15">
                      <th className="py-4 px-6">Electrolyte Formulation</th>
                      <th className="py-4 px-6">Dopant Ratio</th>
                      <th className="py-4 px-6">Grain Size (μm)</th>
                      <th className="py-4 px-6">CCD Threshold</th>
                      <th className="py-4 px-6">Citation</th>
                    </tr>
                  </thead>
                  <tbody className="text-secondary divide-y divide-[#3D8BFF]/10">
                    <TableRow 
                      formula="Standard c-LLZO (Undoped)" 
                      dopant="None" 
                      grain="12.4 ± 1.1" 
                      ccd="4.1 mA/cm²" ccdClass="text-state-error" 
                      citeId="1" 
                    />
                    <TableRow 
                      formula="Ta-doped LLZTO" 
                      dopant="Ta = 0.6 mol" 
                      grain="5.2 ± 0.4" 
                      ccd="8.7 mA/cm²" ccdClass="text-accent-glow drop-shadow-[0_0_8px_rgba(107,168,255,0.4)]" 
                      citeId="2" 
                    />
                    <TableRow 
                      formula="Al/Ta Co-doped Core" 
                      dopant="Al 0.15 / Ta 0.5" 
                      grain="3.1 ± 0.2" 
                      ccd="14.2 mA/cm²" ccdClass="text-state-success drop-shadow-[0_0_8px_rgba(74,222,158,0.4)]" 
                      citeId="3" 
                    />
                    <TableRow 
                      formula="ALD-Interlayer ($Al_2O_3$)" 
                      dopant="Surface 5nm film" 
                      grain="N/A" 
                      ccd="16.8 mA/cm²" ccdClass="text-state-success drop-shadow-[0_0_8px_rgba(74,222,158,0.4)]" 
                      citeId="4" 
                    />
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center justify-between text-text-muted font-citation text-citation pt-5 bg-surface-container/30 border border-[#3D8BFF]/15 p-6 rounded-2xl backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-[17px] text-accent-glow drop-shadow-[0_0_8px_rgba(107,168,255,0.5)]">verified_user</span>
          <span>Cryptographic Hash: <code className="font-mono text-primary tracking-wider font-semibold">0x9F4C...77AE3</code></span>
        </div>
        <div>Model: Anthropic Claude 3.5 Sonnet / ALIE Neural Pipeline v2.4</div>
      </div>
    </article>
  );
};

const CitePill: React.FC<{ id: string }> = ({ id }) => (
  <button className="cite-pill font-citation text-citation ml-1 px-2.5 py-0.5 rounded-full bg-surface-elevated/80 border border-[#3D8BFF]/25 hover:bg-primary hover:text-white transition-all text-accent-glow font-medium shadow-[0_0_12px_rgba(61,139,255,0.25)]">
    [{id}]
  </button>
);

const TakeawayItem: React.FC<{ title: string, text: string }> = ({ title, text }) => (
  <li className="flex items-start gap-4 p-4 rounded-xl bg-surface-container/30 border border-[#3D8BFF]/10">
    <span className="material-symbols-outlined text-accent-glow text-[22px] shrink-0 mt-0.5 drop-shadow-[0_0_8px_rgba(107,168,255,0.5)]">check_circle</span>
    <div>
      <strong className="text-text-primary font-medium block mb-1">{title}</strong>
      <span>{text}</span>
    </div>
  </li>
);

const MetricCard = ({ title, value, unit, subtext, subtextIcon, subtextColor, glow, isSuccess }: any) => (
  <div className="p-5 rounded-xl bg-surface-container/50 border border-[#3D8BFF]/15 backdrop-blur-sm relative overflow-hidden group hover:border-[#3D8BFF]/35 transition-all">
    <div className="font-citation text-[11px] text-text-muted uppercase tracking-widest">{title}</div>
    <div className={`text-3xl font-light mt-2.5 tracking-tight ${glow ? 'text-accent-glow drop-shadow-[0_0_12px_rgba(107,168,255,0.35)]' : isSuccess ? 'text-state-success drop-shadow-[0_0_12px_rgba(74,222,158,0.35)]' : 'text-text-primary'}`}>
      {value} {unit && <span className="text-xs font-normal text-text-muted/80 font-mono">{unit}</span>}
    </div>
    <div className={`text-[11px] font-citation mt-1.5 ${subtextColor || 'text-text-muted/80 font-mono'} ${subtextIcon ? 'flex items-center gap-1 font-medium' : ''}`}>
      {subtextIcon && <span className="material-symbols-outlined text-[13px]">{subtextIcon}</span>}
      {subtext}
    </div>
  </div>
);

const ChartBar = ({ height, label, tooltip, variant = 'default' }: any) => {
  let bgClass = "bg-surface-container/80 group-hover:bg-primary/40 border-t border-[#3D8BFF]/20";
  let textClass = "text-text-muted";
  let tooltipBorder = "border-[#3D8BFF]/30 text-primary";
  
  if (variant === 'warning') {
    bgClass = "bg-gradient-to-t from-primary/80 to-accent-glow group-hover:brightness-125 shadow-[0_0_18px_rgba(61,139,255,0.4)]";
    textClass = "text-accent-glow font-medium";
    tooltipBorder = "border-[#3D8BFF]/40 text-accent-glow shadow-[0_0_14px_rgba(61,139,255,0.4)]";
  } else if (variant === 'danger') {
    bgClass = "bg-gradient-to-t from-state-error/80 to-[#ff8585] group-hover:brightness-125 shadow-[0_0_18px_rgba(255,107,107,0.35)]";
    textClass = "text-state-error font-medium";
    tooltipBorder = "border-state-error/40 text-state-error shadow-[0_0_14px_rgba(255,107,107,0.4)]";
  }

  return (
    <div className="flex-1 flex flex-col items-center gap-2 group relative z-10">
      <div className={`w-full rounded-t-lg transition-all relative ${height} ${bgClass}`}>
        <span className={`hidden group-hover:block absolute -top-8 left-1/2 -translate-x-1/2 bg-[#0D1420] border px-2.5 py-0.5 rounded font-citation text-citation shadow-[0_0_12px_rgba(0,0,0,0.6)] whitespace-nowrap ${tooltipBorder}`}>
          {tooltip}
        </span>
      </div>
      <span className={`font-citation text-citation ${textClass}`}>{label}</span>
    </div>
  );
};

const TableRow = ({ formula, dopant, grain, ccd, ccdClass, citeId }: any) => (
  <tr className="hover:bg-surface-container/40 transition-colors">
    <td className="py-4 px-6 font-medium text-text-primary">{formula}</td>
    <td className="py-4 px-6 font-citation text-citation text-text-muted font-mono">{dopant}</td>
    <td className="py-4 px-6 font-citation text-citation font-mono">{grain}</td>
    <td className={`py-4 px-6 font-citation text-citation font-medium ${ccdClass}`}>{ccd}</td>
    <td className="py-4 px-6">
      <button className="cite-pill font-citation text-citation px-2.5 py-0.5 rounded-full bg-surface-container/90 border border-[#3D8BFF]/25 hover:bg-primary hover:text-white text-accent-glow">
        [{citeId}]
      </button>
    </td>
  </tr>
);
