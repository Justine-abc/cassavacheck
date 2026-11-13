// English and Kinyarwanda. The English text is the key, so a missing translation falls back to English rather than
// showing a blank. Translation changes only the words on screen: what is sent to the API (answers, district) stays the
// English value, so the log and the model never depend on the language chosen.
// Disease names in Kinyarwanda keep the English code beside them (for example "(CBSD)"), so they always match the
// fact sheets and what the officer sees.
const LANGUAGE_KEY = "cassacheck-language";
const LANG = (() => { try { return localStorage.getItem(LANGUAGE_KEY) === "rw" ? "rw" : "en"; } catch { return "en"; } })();
document.documentElement.lang = LANG;

const normaliseKey = (text) => String(text).replace(/\s+/g, " ").trim().replace(/<br\/>/g, "<br>");

function T(text) {
  if (LANG !== "rw") return text;
  return RW[normaliseKey(text)] ?? text;
}

// Static text in the HTML carries a data-t attribute; its English content is looked up once the page has loaded.
function applyTranslations(root = document) {
  if (LANG !== "rw") return;
  root.querySelectorAll("[data-t]").forEach((element) => {
    const key = normaliseKey(element.innerHTML);
    if (key in RW) element.innerHTML = RW[key];
  });
}
document.addEventListener("DOMContentLoaded", () => applyTranslations());

function languageSwitch() {
  const option = (code, label) => `<span class="${LANG === code ? "bg-primary text-on-primary" : "text-on-surface-variant"} px-2 py-1 rounded-md">${label}</span>`;
  return `<button id="language-switch" type="button" class="flex items-center gap-0.5 bg-surface-container-high rounded-lg p-0.5 font-label-md text-label-md"
    aria-label="${LANG === "rw" ? "Change language to English" : "Hindura ururimi ujye mu Kinyarwanda"}">${option("en", "EN")}${option("rw", "RW")}</button>`;
}

function wireLanguageSwitch() {
  const button = document.getElementById("language-switch");
  if (!button) return;
  // A reload redraws every page in the new language; the result page keeps its result in sessionStorage.
  button.onclick = () => { try { localStorage.setItem(LANGUAGE_KEY, LANG === "rw" ? "en" : "rw"); } catch {} window.location.reload(); };
}

// The English district sentence comes from the API; the Kinyarwanda one is built here from the same published row.
function districtSentenceRw(district, rows) {
  const row = rows.find((r) => r.district.toLowerCase() === String(district).toLowerCase());
  if (!row) return `Nta gaciro kavuye mu bushakashatsi kari katangazwa ku karere ka ${district}.`;
  return `${row.district}: mu ibarura ry'igihugu ryo mu ${row.survey_year} (${row.sampling_period}), ${row.cbsd_incidence_pct}% by'ibiti ${row.plants_examined} `
    + `by'imyumbati byasuzumwe byari bifite ibimenyetso bya Kabore (CBSD) ku mababi `
    + `(intera ya 95%: ${row.ci_low_pct} kugeza ${row.ci_high_pct}%). Inkomoko: ${row.source}. Ibi bivuga akarere, si ikibabi cyawe.`;
}

const RW = {
  // Header, navigation, shared pieces
  "Diagnose": "Suzuma",
  "My case": "Dosiye yanjye",
  "How it works": "Uko ikora",
  "Diseases": "Indwara",
  "Back": "Subira inyuma",
  "Confidence": "Icyizere",
  "Decision line": "Umurongo w'icyemezo",
  "Above the line, CassaCheck names a condition.": "Hejuru y'umurongo, CassaCheck ivuga indwara.",
  "Below the line, CassaCheck does not guess: it says not sure.": "Munsi y'umurongo, CassaCheck ntikeka: ivuga ko itabizi neza.",
  "Cassava bacterial blight": "Kirabiranya y'imyumbati",
  "Cassava brown streak disease": "Kabore (ububore bw'imyumbati)",
  "Cassava green mite": "Akarayi k'imyumbati",
  "Cassava mosaic disease": "Ububembe bw'imyumbati",
  "Healthy leaf": "Ikibabi kizima",
  "Check a leaf now": "Suzuma ikibabi ubu",

  // Diagnose page
  "Check a cassava leaf": "Suzuma ikibabi cy'umwumbati",
  "One leaf photo. You get a diagnosis with an honest confidence, or \"not sure\" and the next steps.": "Ifoto y'ikibabi kimwe. Uhabwa igisubizo gifite icyizere nyacyo, cyangwa \"ntibizwi neza\" n'icyo wakora nyuma.",
  "District and season": "Akarere n'igihembwe",
  "District": "Akarere",
  "Choose your district (optional)": "Hitamo akarere kawe (si ngombwa)",
  "Crop season": "Igihembwe cy'ihinga",
  "Used only for the district information panel. It never changes the diagnosis.": "Bikoreshwa gusa ku makuru y'akarere. Ntibihindura na rimwe igisubizo cy'isuzuma.",
  "Season": "Igihembwe",
  "no survey data yet": "nta makuru y'ubushakashatsi arahaboneka",
  "Leaf photo": "Ifoto y'ikibabi",
  "1 photo attached": "Ifoto 1 yongewemo",
  "<b>Field tip:</b> one leaf filling the frame, in daylight, phone held steady.": "<b>Inama:</b> ikibabi kimwe cyuzuye ifoto, ku manywa, telefoni idanyeganyega.",
  "Take or choose a photo": "Fata ifoto cyangwa uyihitemo",
  "JPEG or PNG, up to 10 MB": "JPEG cyangwa PNG, kugeza kuri MB 10",
  ", or drag a photo here": ", cyangwa ukurure ifoto uyizane hano",
  "Retake photo": "Ongera ufate ifoto",
  "No photo at hand? Try one of these, taken in Kicukiro in October 2026:": "Nta foto ufite? Gerageza imwe muri izi, zafatiwe i Kicukiro mu Ukwakira 2026:",
  "Diagnose leaf": "Suzuma ikibabi",
  "Checking the leaf…": "Ikibabi kirimo gusuzumwa…",
  "Looks healthy": "Gisa n'ikizima",
  "Visible symptoms": "Kigaragaza ibimenyetso",
  "Drop a JPEG or PNG photo.": "Shyiramo ifoto ya JPEG cyangwa PNG.",
  "No connection to the server. Check your internet and try again.": "Nta murongo wa seriveri. Reba interineti yawe wongere ugerageze.",
  "The diagnosis failed. Try again.": "Isuzuma ntiryakunze. Ongera ugerageze.",
  "Upload a JPEG or PNG photograph": "Ohereza ifoto ya JPEG cyangwa PNG",
  "Image larger than 10 MB": "Ifoto irengeje MB 10",
  "The file is not a readable image": "Iyi dosiye si ifoto isomeka",
  "This does not look like a leaf photo. Take one cassava leaf filling the frame, in daylight.": "Ibi ntibisa n'ifoto y'ikibabi. Fata ikibabi kimwe cy'umwumbati cyuzuye ifoto, ku manywa.",

  // Result page
  "Diagnosis result": "Igisubizo cy'isuzuma",
  "The leaf you checked": "Ikibabi wasuzumye",
  "Check another leaf": "Suzuma ikindi kibabi",
  "Diagnosis": "Igisubizo",
  "On photos the model did not learn from, answers at this confidence were right about this often.": "Ku mafoto porogaramu itigiyeho, ibisubizo bifite iki cyizere byabaga ari ukuri kuri iki kigero.",
  "All five conditions": "Ibyiciro bitanu byose",
  "What to do": "Icyo wakora",
  "Management advice": "Inama zo kwita ku murima",
  "Management steps only. CassaCheck never recommends a chemical or a dose.": "Ni intambwe zo kwita ku murima gusa. CassaCheck ntijya itanga inama y'umuti cyangwa ingano yawo.",
  "About this disease: cause, spread, prevention": "Ibyerekeye iyi ndwara: icyayiteye, uko ikwirakwira, uko yirindwa",
  "Take another photo": "Fata indi foto",
  "Not sure": "Ntibizwi neza",
  "below the threshold of": "munsi y'urugero rwa",
  "Not sure from this photo": "Ntibizwi neza kuri iyi foto",
  "The model is not confident enough to name a condition for this leaf, so it does not guess. Answer the questions for advice, or send the case to an extension officer. Your answers do not change the diagnosis.":
    "Porogaramu ntifite icyizere gihagije cyo kuvuga indwara y'iki kibabi, bityo ntikeka. Subiza ibibazo uhabwe inama, cyangwa wohereze iki kibazo ku mukozi ushinzwe ubuhinzi. Ibisubizo byawe ntibihindura igisubizo cy'isuzuma.",
  "What do you see in the field?": "Ubona iki mu murima?",
  "questions": "ibibazo",
  "Get advice": "Habwa inama",
  "Details for the extension officer": "Ibisobanuro bigenewe umukozi ushinzwe ubuhinzi",
  "Calibrated probabilities. None reached the threshold, so no condition is named.": "Amahirwe yahujwe n'ukuri. Nta na kimwe cyageze ku rugero, bityo nta ndwara ivugwa.",
  "Your answers do not point to anything specific. Follow the steps below.": "Ibisubizo byawe ntibigaragaza ikintu cyihariye. Kurikiza intambwe ziri hasi.",
  "From your answers": "Ukurikije ibisubizo byawe",
  "What this tells us": "Icyo bitubwira",
  "What to do now": "Icyo wakora ubu",
  "No result yet": "Nta gisubizo kiraboneka",
  "Check a leaf first.": "Banza usuzume ikibabi.",
  "Go to diagnose": "Jya ku isuzuma",
  "District information": "Amakuru y'akarere",
  "This is published survey information for the district. It is not a probability for this leaf and did not change the diagnosis.":
    "Aya ni amakuru y'ubushakashatsi yatangajwe ku karere. Si amahirwe y'iki kibabi kandi ntiyahinduye igisubizo cy'isuzuma.",

  // Referral
  "Send to extension officer": "Ohereza ku mukozi ushinzwe ubuhinzi",
  "Ask an extension officer": "Baza umukozi ushinzwe ubuhinzi",
  "Send to the extension officer": "Ohereza ku mukozi ushinzwe ubuhinzi",
  "The officer sees the result, your district and your answers. Your photo is not sent.": "Umukozi abona igisubizo, akarere kawe n'ibisubizo byawe. Ifoto yawe ntoherezwa.",
  "I agree that the extension officer may call me about this case.": "Nemeye ko umukozi ushinzwe ubuhinzi ampamagara kuri iki kibazo.",
  "Phone number": "Nimero ya telefoni",
  "Used only for this case. It is deleted when the officer answers, or after 30 days.": "Ikoreshwa kuri iki kibazo gusa. Isibwa iyo umukozi amaze gusubiza, cyangwa nyuma y'iminsi 30.",
  "Send": "Ohereza",
  "Enter your phone number, or untick the box.": "Andika nimero ya telefoni yawe, cyangwa ukureho akamenyetso.",
  "Sent to the extension officer.": "Byoherejwe ku mukozi ushinzwe ubuhinzi.",
  "The officer can call you.": "Umukozi ashobora kuguhamagara.",
  "Show this case number to your farmer promoter or sector agronomist.": "Erekana iyi nimero ya dosiye umufashamyumvire w'ubuhinzi cyangwa agronome w'umurenge.",
  "Case number": "Nimero ya dosiye",
  "Check code": "Kode y'igenzura",
  "Write both down or take a screenshot. You need them to read the officer's answer.": "Byandike byombi cyangwa ufotore ekarani. Uzabikenera kugira ngo usome igisubizo cy'umukozi.",
  "Open My case": "Fungura Dosiye yanjye",
  "No answer after 3 days? Go to your sector agronomist's office and show this case number.": "Nta gisubizo nyuma y'iminsi 3? Jya ku biro bya agronome w'umurenge wawe, werekane iyi nimero ya dosiye.",
  "Could not reach the server. Try again.": "Ntibyashobotse kugera kuri seriveri. Ongera ugerageze.",
  "Unknown diagnosis": "Iri suzuma ntirizwi",
  "Tick the consent box to share a phone number, or leave the number empty.": "Shyira akamenyetso ku kwemera kugira ngo utange nimero ya telefoni, cyangwa usige nimero itanditse.",
  "Enter a Rwandan mobile number, for example 0788 123 456.": "Andika nimero ya telefoni yo mu Rwanda, urugero 0788 123 456.",

  // My case page
  "See whether the extension officer has looked at a case you sent, and read their answer.": "Reba niba umukozi ushinzwe ubuhinzi yarebye dosiye wohereje, kandi usome igisubizo cye.",
  "Find a case": "Shaka dosiye",
  "Check status": "Reba aho bigeze",
  "Case": "Dosiye",
  "Updated": "Byavuguruwe",
  "Received": "Yakiriwe",
  "Seen by the officer": "Yarebwe n'umukozi",
  "Visit planned": "Uruzinduko rwateganyijwe",
  "Answered": "Yashubijwe",
  "From the extension officer": "Bivuye ku mukozi ushinzwe ubuhinzi",
  "The officer has not written an answer yet.": "Umukozi ntarandika igisubizo.",
  "Sent from this phone": "Byoherejwe kuri iyi telefoni",
  "Remove from this phone": "Kura kuri iyi telefoni",
  "No case with this number and code. Check both and try again.": "Nta dosiye ifite iyi nimero n'iyi kode. Reba byombi wongere ugerageze.",

  // Advice (api/advice.py)
  "Remove badly affected plants and burn the debris.": "Randura ibiti byafashwe cyane, maze utwike ibisigazwa.",
  "Use clean cuttings from a certified source next season.": "Igihembwe gitaha, koresha ingeri nzima zivuye ahantu hemewe.",
  "Ask the extension officer to confirm before replanting.": "Saba umukozi ushinzwe ubuhinzi kubyemeza mbere yo kongera gutera.",
  "Do not take cuttings from this plant.": "Ntugafate ingeri kuri iki giti.",
  "Use certified, tolerant planting material.": "Koresha imbuto zemewe kandi zihanganira indwara.",
  "Ask the extension officer to confirm; brown streak is easy to confuse with other causes.": "Saba umukozi ushinzwe ubuhinzi kubyemeza; Kabore yitiranywa byoroshye n'izindi mpamvu.",
  "Check the undersides of young leaves for mites.": "Reba munsi y'amababi akiri mato niba hariho uturayi.",
  "Keep the field weeded; mite damage usually eases with the rains.": "Komeza kubagara umurima; ibyangizwa n'uturayi bikunze kugabanuka imvura iguye.",
  "Prefer tolerant varieties next season.": "Igihembwe gitaha, hitamo amoko yihanganira indwara.",
  "Use certified, resistant varieties for the next planting.": "Mu itera ritaha, koresha amoko yemewe kandi arwanya indwara.",
  "Remove heavily affected plants if they are few.": "Randura ibiti byafashwe cyane niba ari bike.",
  "No disease signs detected on this leaf.": "Nta bimenyetso by'indwara byabonetse kuri iki kibabi.",
  "Check other leaves and plants in the field.": "Reba andi mababi n'ibindi biti mu murima.",
  "Keep using clean planting material.": "Komeza gukoresha imbuto nzima.",
  "How old is this leaf?": "Iki kibabi kimaze igihe kingana iki?",
  "Young (top of plant)": "Gikiri gito (hejuru ku giti)",
  "Older (lower on plant)": "Gishaje (hasi ku giti)",
  "Do you see small white flies under the leaves?": "Ubona udusazi duto twera munsi y'amababi?",
  "Yes": "Yego",
  "No": "Oya",
  "Not checked": "Sinabirebye",
  "Do you see any other signs on the plant?": "Ubona ibindi bimenyetso ku giti?",
  "Tiny mites or insects": "Uturayi cyangwa udukoko duto",
  "Spots or cracks on the stem": "Amabara cyangwa imyatuko ku giti",
  "Wilting leaves": "Amababi araraba",
  "None of these": "Nta na kimwe muri ibi",
  "Where did the cuttings come from?": "Ingeri zavuye he?",
  "My own field": "Mu murima wanjye",
  "A neighbour": "Ku muturanyi",
  "Certified seed": "Imbuto zemewe",
  "Whiteflies carry the mosaic and brown streak viruses. Tell the officer you saw them.": "Udusazi twera dukwirakwiza virusi z'ububembe n'iza Kabore. Bwira umukozi ko watubonye.",
  "Mites on young leaves can cause green mite damage. Show the officer the undersides of the leaves.": "Uturayi ku mababi akiri mato dushobora gutera ibyangizwa n'akarayi k'imyumbati. Erekana umukozi munsi y'amababi.",
  "Stem spots can come with bacterial blight. Keep cuttings from this plant out of the next planting.": "Amabara ku giti ashobora kuzanwa na Kirabiranya y'imyumbati. Ntugatere ingeri z'iki giti mu itera ritaha.",
  "Wilting can have several causes, including bacterial blight. The officer should see the plant.": "Kuraba bishobora guterwa n'impamvu nyinshi, harimo Kirabiranya y'imyumbati. Umukozi akwiye kureba iki giti.",
  "Cuttings from your own field can carry viruses from last season. Certified cuttings are safer next season.": "Ingeri zo mu murima wawe zishobora kuzana virusi z'igihembwe gishize. Ingeri zemewe ni zo zizewe igihembwe gitaha.",
  "Cuttings from another field can bring viruses with them. Certified cuttings are safer next season.": "Ingeri zivuye mu wundi murima zishobora kuzana virusi. Ingeri zemewe ni zo zizewe igihembwe gitaha.",
  "Check two more leaves on the same plant and take another photo in daylight.": "Reba andi mababi abiri ku giti kimwe, maze ufate indi foto ku manywa.",
  "Do not take cuttings from this plant until an officer has checked it.": "Ntugafate ingeri kuri iki giti kugeza umukozi akirebye.",
  "Ask your farmer promoter or sector agronomist and show them this result.": "Baza umufashamyumvire w'ubuhinzi cyangwa agronome w'umurenge, ubereke iki gisubizo.",

  // How it works page
  "How CassaCheck works": "Uko CassaCheck ikora",
  "Plain facts about the leaf diagnosis, for farmers and extension officers.": "Ukuri kworoshye ku isuzuma ry'ikibabi, ku bahinzi n'abakozi bashinzwe ubuhinzi.",
  "1 of 3": "1 kuri 3",
  "2 of 3": "2 kuri 3",
  "3 of 3": "3 kuri 3",
  "What the model is": "Porogaramu iyo ari yo",
  "A small image classifier (MobileNetV3-Large) that learned from 14,977 public field photos of cassava leaves taken in Uganda, and was checked on thousands of photos it had never seen, including photos from Ghana. It recognises five conditions:":
    "Ni porogaramu nto itandukanya amafoto (MobileNetV3-Large) yigiye ku mafoto 14,977 rusange y'amababi y'imyumbati yafatiwe mu mirima yo muri Uganda, igasuzumwa ku bihumbi by'amafoto itari yarabonye, harimo amafoto yo muri Ghana. Imenya ibyiciro bitanu:",
  "Bacterial blight (CBB)": "Kirabiranya y'imyumbati (CBB)",
  "Brown streak disease (CBSD)": "Kabore (CBSD)",
  "Green mite damage (CGM)": "Ibyangizwa n'akarayi k'imyumbati (CGM)",
  "Mosaic disease (CMD)": "Ububembe bw'imyumbati (CMD)",
  "Anything else, such as another crop or another disease, is outside what it knows. That is one reason it can say \"not sure\".":
    "Ikindi cyose, nk'ikindi gihingwa cyangwa indi ndwara, kiri hanze y'ibyo izi. Iyo ni imwe mu mpamvu ishobora kuvuga \"ntibizwi neza\".",
  "What \"confidence\" means": "\"Icyizere\" bivuga iki",
  "The confidence is adjusted (calibrated) on photos the model did not learn from, so that 80% means the model was right about 80 times out of 100 on similar photos.":
    "Icyizere gihuzwa n'ukuri ku mafoto porogaramu itigiyeho, ku buryo 80% bivuze ko porogaramu yari ifite ukuri inshuro nka 80 ku 100 ku mafoto asa n'iyi.",
  "<b class=\"text-error\">It is not:</b> how much of your field is infected.": "<b class=\"text-error\">Si:</b> ingano y'umurima wawe yafashwe n'indwara.",
  "<b class=\"text-primary\">It is:</b> how often the model is right on leaves like this one.": "<b class=\"text-primary\">Ni:</b> inshuro porogaramu igira ukuri ku mababi nk'iki.",
  "On photos that look very different from the ones it learned from, for example from another country or camera, the confidence is less reliable. The \"not sure\" answer is the safety net for those cases.":
    "Ku mafoto atandukanye cyane n'ayo yigiyeho, urugero ayo mu kindi gihugu cyangwa ya kamera itandukanye, icyizere ntikiba cyizewe cyane. Igisubizo \"ntibizwi neza\" ni cyo kirinda muri ibyo bihe.",
  "Why it sometimes says \"not sure\"": "Impamvu rimwe na rimwe ivuga \"ntibizwi neza\"",
  "When the confidence is below a threshold fixed in advance, CassaCheck does not guess. It asks a few questions about what you see in the field, gives safe next steps, and lets you send the case to an extension officer. The threshold is set so that it answers about 8 photos in 10 of the kind it was tested on.":
    "Iyo icyizere kiri munsi y'urugero rwashyizweho mbere, CassaCheck ntikeka. Ikubaza ibibazo bike ku byo ubona mu murima, ikaguha intambwe zizewe zo gukurikiza, kandi ikakwemerera kohereza ikibazo ku mukozi ushinzwe ubuhinzi. Urugero rwashyizweho ku buryo isubiza amafoto agera ku 8 kuri 10 y'ubwoko yagerageweho.",
  "Safety rules": "Amategeko y'umutekano",
  "A wrong answer that sounds certain is worse than an honest \"not sure\".": "Igisubizo kitari cyo kivuganye icyizere kibi kurusha \"ntibizwi neza\" kivugishije ukuri.",
  "A photo with too little leaf colour, such as a screenshot or a wall, is refused before the model looks at it.": "Ifoto ifite ibara rito ry'ikibabi, nk'ifoto ya ekarani cyangwa urukuta, yangwa mbere y'uko porogaramu iyireba.",
  "Advice is management steps only. It never names a chemical or a dose.": "Inama ni intambwe zo kwita ku murima gusa. Ntijya ivuga umuti cyangwa ingano yawo.",
  "District survey information is shown beside the result and never changes the diagnosis.": "Amakuru y'ubushakashatsi bw'akarere agaragara iruhande rw'igisubizo kandi ntahindura na rimwe igisubizo cy'isuzuma.",
  "Photos are not stored. The officer's list keeps district, season, result and your answers. A phone number is kept only if you agree, and is deleted when the officer answers or after 30 days.":
    "Amafoto ntabikwa. Urutonde rw'umukozi rubika akarere, igihembwe, igisubizo n'ibisubizo byawe. Nimero ya telefoni ibikwa gusa iyo wabyemeye, kandi isibwa iyo umukozi amaze gusubiza cyangwa nyuma y'iminsi 30.",
  "Field practice": "Mu murima",
  "Photo rules for a clear result": "Amabwiriza y'ifoto kugira ngo ubone igisubizo gisobanutse",
  "<b>One leaf</b><br><span class=\"font-body-sm text-body-sm\">Photograph one leaf with symptoms, not the whole plant.</span>":
    "<b>Ikibabi kimwe</b><br><span class=\"font-body-sm text-body-sm\">Fotora ikibabi kimwe gifite ibimenyetso, si igiti cyose.</span>",
  "<b>Fill the screen</b><br><span class=\"font-body-sm text-body-sm\">Hold the phone 15 to 20 cm away so the leaf fills the frame.</span>":
    "<b>Uzuza ekarani</b><br><span class=\"font-body-sm text-body-sm\">Fata telefoni kuri cm 15 kugeza kuri 20 kugira ngo ikibabi cyuzure ifoto.</span>",
  "<b>Daylight, no shadow</b><br><span class=\"font-body-sm text-body-sm\">Avoid harsh midday sun and your own shadow on the leaf.</span>":
    "<b>Ku manywa, nta gicucu</b><br><span class=\"font-body-sm text-body-sm\">Irinde izuba ryinshi rya saa sita n'igicucu cyawe ku kibabi.</span>",
  "Extension officer? Sign in to see referred cases": "Uri umukozi ushinzwe ubuhinzi? Injira urebe dosiye zoherejwe",

  // Diseases page (every English line is from the linked fact sheet)
  "Cassava diseases": "Indwara z'imyumbati",
  "The four conditions CassaCheck recognises: what causes them, what you see, how they spread and how to prevent them.":
    "Ibyiciro bine CassaCheck imenya: icyabiteye, ibyo ubona, uko bikwirakwira n'uko byirindwa.",
  "Cause:": "Icyayiteye:",
  "What you see": "Ibyo ubona",
  "How it spreads": "Uko ikwirakwira",
  "Prevent it, without chemicals": "Uko wayirinda, nta miti",
  "Look-alike:": "Isa na:",
  "Source:": "Inkomoko:",
  "The same three habits protect against all four": "Imico itatu imwe irinda izi ndwara uko ari enye",
  "Clean cuttings": "Ingeri nzima",
  "Plant only stems from healthy plants or certified material.": "Tera gusa ingeri zivuye ku biti bizima cyangwa imbuto zemewe.",
  "Remove sick plants early": "Randura ibiti birwaye hakiri kare",
  "The sooner a sick plant is out, the less it spreads.": "Uko igiti kirwaye kirandurwa vuba, ni ko indwara ikwirakwira gake.",
  "Tolerant varieties": "Amoko yihanganira indwara",
  "Ask your farmer promoter or sector agronomist which varieties suit your area.": "Baza umufashamyumvire w'ubuhinzi cyangwa agronome w'umurenge amoko akwiriye agace kawe.",
  "Viruses (cassava mosaic viruses).": "Virusi (virusi z'ububembe bw'imyumbati).",
  "Pale green to yellow patches on the leaves, a pattern called a mosaic.": "Amabara y'icyatsi cyerurutse kugeza ku muhondo ku mababi, ishusho yitwa mozayike.",
  "Leaves and shoots twisted or deformed; the plant may stay small.": "Amababi n'imishibuka biba bigoramye cyangwa byahindutse ishusho; igiti gishobora kuguma ari gito.",
  "Stem cuttings taken from sick plants and shared between farmers.": "Ingeri zifashwe ku biti birwaye zigasangirwa n'abahinzi.",
  "Whiteflies feeding on the leaves.": "Udusazi twera turya ku mababi.",
  "Take cuttings only from plants without symptoms. Never plant stems from a sick plant.": "Fata ingeri gusa ku biti bitagaragaza ibimenyetso. Ntuzigere utera ingeri z'igiti kirwaye.",
  "Pull out sick plants as soon as you see symptoms. Done early, the plants around them make up the lost yield.": "Randura ibiti birwaye ukimara kubona ibimenyetso. Iyo bikozwe kare, ibiti bibikikije byishyura umusaruro watakaye.",
  "Plant resistant varieties.": "Tera amoko arwanya indwara.",
  "Two viruses (cassava brown streak virus and Ugandan cassava brown streak virus).": "Virusi ebyiri (cassava brown streak virus na Ugandan cassava brown streak virus).",
  "Yellow patches along the side veins of older leaves, often joining together.": "Amabara y'umuhondo ku mitsi yo ku ruhande y'amababi ashaje, akenshi ahura.",
  "Dark streaks on young green stems, not always visible.": "Imirongo yijimye ku giti gikiri gito kibisi, itagaragara buri gihe.",
  "Roots smaller than normal, with dark brown dry rot inside when cut.": "Ibijumba bito kurusha ibisanzwe, bifite ukubora kwumye kw'ikigina imbere iyo ubikase.",
  "Whiteflies, over short distances.": "Udusazi twera, ahantu hegeranye.",
  "Planting material moved between farmers, over long distances.": "Imbuto zimurwa hagati y'abahinzi, ahantu hari kure.",
  "Take cuttings only from plants you watched for symptoms during the season.": "Fata ingeri gusa ku biti wakurikiranye ureba ibimenyetso mu gihembwe.",
  "Use certified, virus-cleaned planting material.": "Koresha imbuto zemewe zasukuweho virusi.",
  "Remove plants with leaf or stem symptoms, and burn their stems after harvest.": "Randura ibiti bifite ibimenyetso ku mababi cyangwa ku giti, kandi utwike ibiti byabyo nyuma y'isarura.",
  "Plant tolerant varieties where they are available. Neighbours removing sick plants together works best.": "Tera amoko yihanganira indwara aho aboneka. Abaturanyi barandurira hamwe ibiti birwaye ni bwo bigira akamaro kurushaho.",
  "A bacterium (Xanthomonas axonopodis pv. manihotis).": "Bagiteri (Xanthomonas axonopodis pv. manihotis).",
  "Angular, water-soaked spots between the veins, best seen under the leaf.": "Utudomo dufite inguni, dusa n'utwatose, hagati y'imitsi, tugaragara neza munsi y'ikibabi.",
  "Spots grow, join, and turn brown with yellow edges.": "Utudomo turakura, tugahura, tugahinduka ikigina dufite impande z'umuhondo.",
  "Leaves wilt and fall; stem tips turn black.": "Amababi araraba akagwa; impera z'ibiti zigahinduka umukara.",
  "Rain blown by the wind, and tools such as knives and hoes, over short distances.": "Imvura itwawe n'umuyaga, n'ibikoresho nk'imihoro n'amasuka, ahantu hegeranye.",
  "Infected cuttings, over long distances.": "Ingeri zanduye, ahantu hari kure.",
  "Take cuttings only from healthy fields. Do not plant next to, or downwind of, a sick field.": "Fata ingeri gusa mu mirima mizima. Ntugatere iruhande rw'umurima urwaye, cyangwa aho umuyaga uwuturukamo ugana.",
  "When only a few plants are sick, remove them in dry weather. Clean your tools and keep animals out.": "Iyo ibiti birwaye ari bike, birandure mu gihe cy'izuba. Sukura ibikoresho byawe kandi ubuze amatungo kwinjira.",
  "After harvest, burn or bury old stems you are not keeping for planting.": "Nyuma y'isarura, twika cyangwa uhambe ibiti bishaje utazakoresha mu gutera.",
  "Do not plant cassava again on the same land after a sick crop; wait one to two years.": "Ntukongere gutera imyumbati ku butaka bumwe nyuma y'imyaka yarwaye; tegereza umwaka umwe kugeza ku myaka ibiri.",
  "A tiny mite (Mononychellus tanajoa) that sucks juice from the leaves, mostly from the underside.": "Akarayi gato cyane (Mononychellus tanajoa) kanyunyuza amazi y'amababi, cyane cyane munsi yayo.",
  "Small yellow spots, then yellowing and mottled leaves that die and fall.": "Utudomo duto tw'umuhondo, hanyuma amababi agahinduka umuhondo n'amabara, agapfa akagwa.",
  "Shoot tips lost, leaving a bare stem like a candle.": "Impera z'imishibuka zirashira, igiti kigasigara cyambaye ubusa nk'buji.",
  "Worst in the dry season: rain washes the mites off the leaves.": "Bikabije mu gihe cy'izuba: imvura yoza uturayi ku mababi.",
  "Mites walking between plants, or carried by wind and water.": "Uturayi tugenda hagati y'ibiti, cyangwa dutwawe n'umuyaga n'amazi.",
  "People moving cuttings and leaves, over long distances.": "Abantu bimura ingeri n'amababi, ahantu hari kure.",
  "Take planting material from healthy plants.": "Fata imbuto ku biti bizima.",
  "Plant early in the rainy season.": "Tera kare mu gihe cy'imvura.",
  "Plant mite-tolerant varieties. Predatory mites that eat green mites are the main natural control.": "Tera amoko yihanganira akarayi k'imyumbati. Uturayi turya akarayi k'imyumbati ni bwo buryo nyamukuru kamere bwo kukarwanya.",
  "Easy to confuse with mosaic disease. Mosaic gives yellow and green patches that are not limited to the veins and twists the leaf.":
    "Yitiranywa byoroshye n'ububembe. Ububembe butera amabara y'umuhondo n'icyatsi atagarukira ku mitsi kandi bugoreka ikibabi.",
  // Menu, home banner, progress steps and example photos (November 2026).
  "Main menu": "Ibikubiyemo",
  "Extension officer sign-in": "Kwinjira k'umukozi ushinzwe ubuhinzi",
  "Officer sign-in": "Kwinjira k'umukozi",
  "Honest confidence": "Icyizere nyacyo",
  "Says \"not sure\" instead of guessing": "Ivuga \"ntibizwi neza\" aho gukeka",
  "Extension officer follow-up": "Gukurikiranwa n'umukozi ushinzwe ubuhinzi",
  "Photo: cassava leaf, Kicukiro, October 2026": "Ifoto: ikibabi cy'umwumbati, Kicukiro, Ukwakira 2026",
  "Photo sent": "Ifoto yoherejwe",
  "Checking that the photo shows a leaf": "Kureba ko ifoto igaragaza ikibabi",
  "Comparing with the five conditions": "Kugereranya n'ibyiciro bitanu",
  "Measuring confidence against the decision line": "Gupima icyizere ugereranyije n'umurongo w'icyemezo",
  "Example of": "Urugero rwa",
  "Example photo: CCMT dataset, Ghana (Mensah et al., 2023), CC BY 4.0": "Ifoto y'urugero: amafoto ya CCMT, Ghana (Mensah et al., 2023), CC BY 4.0",
  "No example photo yet: the open photo set used here has no brown streak class.": "Nta foto y'urugero iraboneka: amafoto rusange akoreshwa hano nta Kabore (CBSD) arimo.",
  "Your leaf": "Ikibabi cyawe",
  "Known example": "Urugero ruzwi",
  "Compare the two. If they look very different, take another photo or ask an extension officer.": "Gereranya byombi. Niba bitandukanye cyane, fata indi foto cyangwa ubaze umukozi ushinzwe ubuhinzi.",
};
