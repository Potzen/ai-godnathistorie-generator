// Fil: static/modules/skolekobling.js
//
// Broen mellem skolen og hjemmet. Bruges af Hjemmelæsning til at vise
// ugens fokus og tage imod forælderens kvittering for, at der er læst.
//
// Alt heri fejler stille: en familie, der bruger appen privat, er ikke
// tilmeldt nogen klasse, og så skal siden bare se ud som før.

import { mitUgefokusApi, gemHjemmelaesningApi } from './api_client.js';

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

/** Viser ugens fokus, hvis barnet er tilmeldt en klasse med et fokus sat. */
export async function visUgensFokus() {
    const sektion = document.getElementById('ugens-fokus-sektion');
    if (!sektion) return null;

    let svar;
    try {
        svar = await mitUgefokusApi();
    } catch {
        return null;   // Ikke logget ind, eller ingen forbindelse. Ingen støj.
    }

    const fokus = svar && svar.fokus;
    if (!fokus || !(fokus.lyde || []).length) return null;

    const besked = document.getElementById('ugens-fokus-besked');
    if (besked) {
        besked.textContent = fokus.besked_hjem
            || `I denne uge øver klassen ${fokus.position_navn}.`;
    }

    const liste = document.getElementById('ugens-fokus-lyde');
    if (liste) {
        liste.innerHTML = fokus.lyde
            .map(l => `<span class="fokus-lyd">${esc(l)}</span>`).join('');
    }

    sektion.classList.remove('hidden');
    return fokus;
}

/** Kvittering for dagens læsning. Ét tryk, og så er den gemt. */
export function opsaetLaesekvittering() {
    const boks = document.getElementById('laest-i-dag');
    if (!boks) return;

    boks.addEventListener('click', async (event) => {
        const knap = event.target.closest('[data-laest-af]');
        if (!knap || knap.disabled) return;

        const svar = document.getElementById('laesekvittering-svar');
        boks.querySelectorAll('[data-laest-af]').forEach(k => { k.disabled = true; });

        try {
            await gemHjemmelaesningApi({
                laest_af: knap.dataset.laestAf,
                story_id: window.__sidsteHistorieId || null,
            });
            if (svar) {
                svar.textContent = 'Noteret. Tak fordi I læste sammen.';
                svar.classList.remove('hidden');
            }
        } catch (fejl) {
            boks.querySelectorAll('[data-laest-af]').forEach(k => { k.disabled = false; });
            if (svar) {
                svar.textContent = `Kunne ikke gemme: ${fejl.message}`;
                svar.classList.remove('hidden');
            }
        }
    });
}

/** Viser kvitterings-boksen, når der faktisk er læst en historie. */
export function visLaesekvittering(storyId) {
    window.__sidsteHistorieId = storyId || null;
    document.getElementById('laest-i-dag')?.classList.remove('hidden');
}
