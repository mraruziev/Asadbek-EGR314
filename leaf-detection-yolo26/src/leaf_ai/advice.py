"""Treatment guidance for each class the classifier can return.

A diagnosis on its own is not actionable -- "Tomato: Late blight 94%" only helps someone
who already knows what late blight means. Each entry pairs the pathogen with what to
actually do, and flags the few diseases where a slow response loses the crop.

This is general agronomic guidance. Product availability, approved actives and
notification requirements vary by country, so the caller should confirm locally before
spraying anything. Citrus greening in particular is a notifiable disease in many regions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Advice:
    cause: str
    urgency: str  # "none", "routine", or "urgent"
    actions: tuple[str, ...] = field(default_factory=tuple)


HEALTHY = Advice(
    cause="No disease signs detected.",
    urgency="none",
    actions=("Keep scouting on your normal schedule.", "Avoid overhead watering late in the day."),
)

NOT_A_LEAF = Advice(
    cause="No plant material identified in the image.",
    urgency="none",
    actions=("Retake the photo with a single leaf filling most of the frame.",),
)

ADVICE: dict[str, Advice] = {
    "Apple_Apple_scab": Advice(
        "Fungus (Venturia inaequalis). Spreads from fallen leaves in wet spring weather.",
        "routine",
        ("Rake and destroy fallen leaves to break the overwintering cycle.",
         "Protectant fungicide from green tip through petal fall.",
         "Prune for airflow; plant scab-resistant cultivars when replanting."),
    ),
    "Apple_Black_rot": Advice(
        "Fungus (Botryosphaeria obtusa). Overwinters in cankers and mummified fruit.",
        "routine",
        ("Prune out cankers and dead wood; remove mummified fruit.",
         "Fungicide at petal fall and through cover sprays.",
         "Burn or bin prunings -- do not compost them near the orchard."),
    ),
    "Apple_Cedar_apple_rust": Advice(
        "Fungus (Gymnosporangium juniperi-virginianae). Needs a nearby juniper or cedar to complete its cycle.",
        "routine",
        ("Remove juniper/cedar hosts within a few hundred metres if practical.",
         "Fungicide from pink bud until about two weeks after petal fall.",
         "Choose resistant cultivars when replanting."),
    ),
    "Cherry_including_sour_Powdery_mildew": Advice(
        "Fungus (Podosphaera clandestina). Favoured by warm days, humid nights, dense canopies.",
        "routine",
        ("Prune to open the canopy and cut humidity.",
         "Sulfur or potassium bicarbonate sprays on a protectant schedule.",
         "Avoid heavy nitrogen, which pushes susceptible new growth."),
    ),
    "Corn_maize_Cercospora_leaf_spot_Gray_leaf_spot": Advice(
        "Fungus (Cercospora zeae-maydis). Survives on surface residue; worst in no-till continuous corn.",
        "routine",
        ("Rotate out of corn for at least one season.",
         "Bury or remove residue where tillage is an option.",
         "Resistant hybrids; fungicide at VT-R1 if lesions reach the ear leaf."),
    ),
    "Corn_maize_Common_rust": Advice(
        "Fungus (Puccinia sorghi). Usually cosmetic on field corn.",
        "routine",
        ("Normally no treatment needed on field corn.",
         "Resistant hybrids matter more in sweet corn.",
         "Spray only if infection is early, heavy, and on a susceptible hybrid."),
    ),
    "Corn_maize_Northern_Leaf_Blight": Advice(
        "Fungus (Exserohilum turcicum). Long grey-green cigar-shaped lesions.",
        "routine",
        ("Resistant hybrids are the main control.",
         "Rotate and manage residue.",
         "Fungicide near tasseling if lesions appear below the ear leaf before silking."),
    ),
    "Grape_Black_rot": Advice(
        "Fungus (Guignardia bidwellii). Overwinters in mummified berries and canes.",
        "routine",
        ("Remove every mummy from the vine and the ground.",
         "Fungicide from early shoot growth through fruit set -- the critical window.",
         "Open the canopy so leaves dry quickly after rain."),
    ),
    "Grape_Esca_Black_Measles": Advice(
        "Trunk disease complex. There is no curative treatment once vines are infected.",
        "routine",
        ("Prune out symptomatic wood in dry weather only.",
         "Seal large pruning wounds; they are the infection route.",
         "Remove and replace collapsed vines."),
    ),
    "Grape_Leaf_blight_Isariopsis_Leaf_Spot": Advice(
        "Fungus (Pseudocercospora vitis). Late-season leaf spotting.",
        "routine",
        ("Improve canopy airflow and leaf-drying time.",
         "Remove infected leaves and fallen debris.",
         "Standard vineyard fungicide programme usually covers it."),
    ),
    "Orange_Haunglongbing_Citrus_greening": Advice(
        "Bacterium (Candidatus Liberibacter) spread by the Asian citrus psyllid. Incurable and fatal to the tree.",
        "urgent",
        ("There is no cure. Infected trees decline and become a source of spread.",
         "Report it -- citrus greening is a notifiable disease in many regions.",
         "Remove and destroy infected trees; control psyllids; plant only certified stock."),
    ),
    "Peach_Bacterial_spot": Advice(
        "Bacterium (Xanthomonas arboricola pv. pruni). Worst in warm, windy, wet weather.",
        "routine",
        ("Copper at dormancy and early season; copper injures foliage later on.",
         "Resistant cultivars are the durable fix.",
         "Avoid overhead irrigation and shelter the block from wind-driven rain."),
    ),
    "Pepper_bell_Bacterial_spot": Advice(
        "Bacterium (Xanthomonas spp.). Seed- and splash-borne.",
        "routine",
        ("Start from certified disease-free seed and transplants.",
         "Copper plus mancozeb on a protectant schedule.",
         "Never work the rows while foliage is wet; rotate 2-3 years."),
    ),
    "Potato_Early_blight": Advice(
        "Fungus (Alternaria solani). Hits older, stressed foliage first.",
        "routine",
        ("Keep nitrogen adequate -- hungry plants get hit hardest.",
         "Chlorothalonil or mancozeb on a protectant schedule.",
         "Rotate and destroy volunteers and cull piles."),
    ),
    "Potato_Late_blight": Advice(
        "Oomycete (Phytophthora infestans). The Irish famine pathogen. Destroys a field in days under cool wet weather.",
        "urgent",
        ("Act now -- this moves faster than any other disease here.",
         "Destroy infected foliage; do not leave cull piles.",
         "Apply protectant fungicide immediately and keep the interval tight in wet weather.",
         "Kill vines before harvest so tubers are not infected on the way in."),
    ),
    "Squash_Powdery_mildew": Advice(
        "Fungus (Podosphaera xanthii). Thrives in warm days with humid nights, unlike most fungi it does not need leaf wetness.",
        "routine",
        ("Sulfur, potassium bicarbonate or horticultural oil at first white spots.",
         "Space and prune for airflow; water at the base.",
         "Resistant varieties are widely available."),
    ),
    "Strawberry_Leaf_scorch": Advice(
        "Fungus (Diplocarpon earlianum). Dark purple blotches that merge and scorch the leaf.",
        "routine",
        ("Mow and remove old foliage at renovation.",
         "Improve airflow; avoid overhead irrigation.",
         "Fungicide on new growth if pressure is high."),
    ),
    "Tomato_Bacterial_spot": Advice(
        "Bacterium (Xanthomonas spp.). Seed-borne and splash-spread.",
        "routine",
        ("Certified seed and clean transplants matter more than any spray.",
         "Copper-based protectant; rotate 2-3 years.",
         "Stay out of the rows when plants are wet."),
    ),
    "Tomato_Early_blight": Advice(
        "Fungus (Alternaria solani). Target-like rings on lower leaves first.",
        "routine",
        ("Remove affected lower leaves and mulch to stop soil splash.",
         "Chlorothalonil or mancozeb on a protectant schedule.",
         "Stake for airflow; rotate away from tomato and potato."),
    ),
    "Tomato_Late_blight": Advice(
        "Oomycete (Phytophthora infestans). Greasy grey-green lesions; collapses plants in days.",
        "urgent",
        ("Act now -- whole plantings are lost in under a week in cool wet weather.",
         "Pull and destroy infected plants; do not compost them.",
         "Protectant fungicide immediately on anything still clean.",
         "Never water overhead while blight is active."),
    ),
    "Tomato_Leaf_Mold": Advice(
        "Fungus (Passalora fulva). Mainly a greenhouse and high-tunnel problem.",
        "routine",
        ("Drop the humidity -- ventilate, heat, and space the plants.",
         "Remove affected leaves; prune the lower canopy.",
         "Resistant cultivars where mould is a recurring issue."),
    ),
    "Tomato_Septoria_leaf_spot": Advice(
        "Fungus (Septoria lycopersici). Many small spots with pale centres and dark margins.",
        "routine",
        ("Strip infected lower leaves as soon as spots appear.",
         "Mulch to block soil splash; water at the base.",
         "Fungicide and a 2-3 year rotation."),
    ),
    "Tomato_Spider_mites_Two-spotted_spider_mite": Advice(
        "A pest, not a disease (Tetranychus urticae). Stippled leaves and fine webbing.",
        "routine",
        ("Raise humidity and hose down the undersides of leaves.",
         "Insecticidal soap or horticultural oil; repeat on a short interval.",
         "Avoid broad-spectrum insecticides -- they kill the predatory mites and make it worse."),
    ),
    "Tomato_Target_Spot": Advice(
        "Fungus (Corynespora cassiicola). Spots with concentric rings on leaves, stems and fruit.",
        "routine",
        ("Improve airflow and remove crop debris.",
         "Protectant fungicide on a regular interval.",
         "Rotate away from tomato."),
    ),
    "Tomato_Tomato_Yellow_Leaf_Curl_Virus": Advice(
        "Virus spread by whitefly. No cure once a plant is infected.",
        "urgent",
        ("Remove infected plants -- they are a reservoir for the whole planting.",
         "Control whitefly; that is the only way to stop spread.",
         "Resistant varieties and reflective mulch for the next crop."),
    ),
    "Tomato_Tomato_mosaic_virus": Advice(
        "Virus. Extremely stable and spread mechanically by hands and tools.",
        "urgent",
        ("Remove and destroy infected plants.",
         "Wash hands and disinfect tools between plants; tobacco users especially.",
         "Resistant cultivars; never handle plants when wet."),
    ),
}


# PlantWild adds ~95 diseases beyond PlantVillage's 38. Writing a hand-checked entry for
# every one is not realistic, but the disease *type* is recoverable from the name and
# carries most of the actionable content: mildews want airflow, blights want urgency,
# viruses want roguing and vector control. Checked in order, longest phrases first.
GENERIC_BY_KEYWORD: tuple[tuple[str, Advice], ...] = (
    ("downy mildew", Advice(
        "Oomycete downy mildew. Needs leaf wetness; spreads fast in cool humid weather.",
        "urgent",
        ("Stop overhead watering and improve airflow immediately.",
         "Apply an oomycete-active fungicide -- powdery mildew products do not work on downy mildew.",
         "Remove and destroy infected foliage; rotate next season."),
    )),
    ("powdery mildew", Advice(
        "Powdery mildew fungus. Unusually, it does not need leaf wetness -- warm days and humid nights are enough.",
        "routine",
        ("Sulfur, potassium bicarbonate or horticultural oil at the first white patches.",
         "Prune and space for airflow; water at the base.",
         "Choose resistant varieties where available."),
    )),
    ("late blight", Advice(
        "Phytophthora late blight. Destroys plantings within days in cool wet weather.",
        "urgent",
        ("Act now; remove and destroy infected plants, do not compost.",
         "Protectant fungicide on everything still clean.",
         "Never irrigate overhead while blight is active."),
    )),
    ("blight", Advice(
        "Foliar blight. Lesions expand and merge, killing leaf tissue.",
        "routine",
        ("Remove affected leaves and crop debris.",
         "Protectant fungicide on a regular interval.",
         "Rotate and avoid overhead irrigation."),
    )),
    ("mosaic virus", Advice(
        "Plant virus. No cure; spread mechanically and by insect vectors.",
        "urgent",
        ("Remove and destroy infected plants -- they are a reservoir.",
         "Disinfect hands and tools between plants.",
         "Use resistant varieties and control insect vectors."),
    )),
    ("virus", Advice(
        "Plant virus. No cure once a plant is infected.",
        "urgent",
        ("Rogue out infected plants promptly.",
         "Control the insect vector -- that is what stops spread.",
         "Plant certified stock and resistant varieties next season."),
    )),
    ("anthracnose", Advice(
        "Anthracnose fungus. Sunken dark lesions on leaves, stems and fruit; splash-spread.",
        "routine",
        ("Remove infected tissue and fallen debris.",
         "Protectant fungicide through wet weather.",
         "Improve drainage and airflow; avoid overhead watering."),
    )),
    ("rust", Advice(
        "Rust fungus. Orange to brown pustules that release spores when rubbed.",
        "routine",
        ("Remove badly infected leaves; clear debris at end of season.",
         "Fungicide if it reaches the upper canopy early.",
         "Resistant varieties and wider spacing reduce recurrence."),
    )),
    ("leaf spot", Advice(
        "Leaf-spot pathogen. Discrete lesions that merge and defoliate under pressure.",
        "routine",
        ("Strip affected lower leaves and mulch to stop soil splash.",
         "Protectant fungicide on a regular interval.",
         "Rotate away from the same crop family."),
    )),
    ("rot", Advice(
        "Rot pathogen. Tissue breakdown, often starting at wounds or in wet conditions.",
        "routine",
        ("Remove and destroy affected tissue and fallen fruit.",
         "Improve drainage and airflow; avoid injuring plants.",
         "Protectant fungicide where an approved product exists."),
    )),
    ("scab", Advice(
        "Scab fungus. Corky or olive-brown lesions on leaves and fruit.",
        "routine",
        ("Clear fallen leaves to break the overwintering cycle.",
         "Protectant fungicide during the early-season infection window.",
         "Resistant cultivars when replanting."),
    )),
    ("bacterial spot", Advice(
        "Bacterial spot. Seed- and splash-borne; copper is protectant only, never curative.",
        "routine",
        ("Start from certified seed and clean transplants.",
         "Copper-based protectant on a regular interval.",
         "Never work the rows while foliage is wet; rotate 2-3 years."),
    )),
    ("bacterial wilt", Advice(
        "Bacterial wilt, usually vectored by cucumber beetles. Plants wilt with no recovery overnight.",
        "urgent",
        ("Remove wilting plants immediately -- they infect the beetles that move on.",
         "Control cucumber beetles; that is the only real lever.",
         "Resistant varieties and floating row covers on young plants."),
    )),
    ("bacterial leaf streak", Advice(
        "Bacterial leaf streak. Water-soaked streaks that turn necrotic; no in-season chemical control.",
        "routine",
        ("No effective spray -- manage with resistant varieties and rotation.",
         "Avoid overhead irrigation and reduce leaf injury.",
         "Bury residue where tillage is an option."),
    )),
    ("canker", Advice(
        "Bacterial canker. Raised corky lesions; regulated in many citrus regions.",
        "urgent",
        ("Check local rules -- citrus canker is notifiable in many regions.",
         "Remove and destroy infected material; disinfect tools between trees.",
         "Copper protectant and windbreaks to limit wind-driven spread."),
    )),
    ("greening", Advice(
        "Citrus greening (Huanglongbing), spread by psyllids. Incurable and fatal.",
        "urgent",
        ("There is no cure; infected trees are a source of spread.",
         "Report it -- notifiable in many regions.",
         "Remove infected trees, control psyllids, plant certified stock."),
    )),
    ("black leaf streak", Advice(
        "Black Sigatoka (Mycosphaerella fijiensis). The most damaging banana leaf disease.",
        "urgent",
        ("Remove and destroy affected leaves to cut inoculum.",
         "Fungicide programme with rotated modes of action -- resistance builds fast.",
         "Improve drainage and spacing; avoid dense plantings."),
    )),
    ("bunchy top", Advice(
        "Banana bunchy top virus, spread by banana aphid. Incurable.",
        "urgent",
        ("Destroy infected mats entirely, including the corm.",
         "Control banana aphid before and during removal.",
         "Plant only certified virus-free suckers or tissue culture."),
    )),
    ("panama disease", Advice(
        "Fusarium wilt (Panama disease). Soil-borne and persists for decades.",
        "urgent",
        ("Do not replant bananas in affected ground -- the fungus survives for decades.",
         "Quarantine the block; clean soil off boots, tools and machinery.",
         "Resistant cultivars are the only long-term option."),
    )),
    ("leafroll", Advice(
        "Grapevine leafroll virus, spread by mealybugs. No cure.",
        "urgent",
        ("Remove and replace infected vines; they will not recover.",
         "Control mealybugs, which move the virus vine to vine.",
         "Plant certified virus-tested material."),
    )),
    ("smut", Advice(
        "Smut fungus. Galls or spore masses replacing normal tissue.",
        "routine",
        ("Remove and destroy galls before they rupture and release spores.",
         "Resistant varieties and clean certified seed.",
         "Rotate; avoid mechanical injury during cultivation."),
    )),
    ("mummy berry", Advice(
        "Mummy berry (Monilinia). Overwinters in mummified fruit on the ground.",
        "routine",
        ("Remove mummified berries and cultivate lightly to bury them.",
         "Fungicide at bud break through bloom.",
         "Mulch to block spores emerging from the soil surface."),
    )),
    ("tar spot", Advice(
        "Tar spot fungus. Raised black spots; mainly cosmetic on shade trees.",
        "routine",
        ("Rake and destroy fallen leaves -- that is where it overwinters.",
         "Usually cosmetic on mature trees; spraying is rarely justified.",
         "Improve airflow where practical."),
    )),
    ("leaf curl", Advice(
        "Peach leaf curl (Taphrina deformans). Infects at bud swell, before symptoms show.",
        "routine",
        ("Timing is everything -- spray at dormancy or bud swell, not after curling appears.",
         "Once leaves are distorted, nothing helps until next season.",
         "Remove affected leaves; keep the tree well fed."),
    )),
    ("pocket disease", Advice(
        "Plum pocket (Taphrina). Distorted hollow fruit, same timing rules as peach leaf curl.",
        "routine",
        ("Dormant fungicide before bud swell is the only effective window.",
         "Remove and destroy distorted fruit.",
         "Prune for airflow."),
    )),
    ("gray mold", Advice(
        "Botrytis grey mould. Thrives on dense wet canopies and damaged tissue.",
        "routine",
        ("Remove infected fruit and dead tissue promptly.",
         "Improve airflow; avoid overhead watering.",
         "Fungicide through bloom in wet seasons."),
    )),
    ("blue mold", Advice(
        "Blue mould (Peronospora). A downy-mildew type pathogen; explosive in cool damp weather.",
        "urgent",
        ("Use an oomycete-active fungicide, not a powdery mildew product.",
         "Increase ventilation and reduce leaf wetness.",
         "Destroy infected seedlings rather than transplanting them."),
    )),
    ("blast", Advice(
        "Rice blast (Magnaporthe oryzae). Diamond-shaped lesions; can take the whole neck and panicle.",
        "urgent",
        ("Fungicide at boot and heading if pressure is high -- neck blast destroys yield.",
         "Avoid excess nitrogen, which strongly increases susceptibility.",
         "Resistant varieties and clean seed."),
    )),
    ("scorch", Advice(
        "Leaf scorch. Marginal browning from fungal infection or water stress.",
        "routine",
        ("Remove affected foliage; renovate beds after harvest.",
         "Check irrigation -- scorch is often water stress, not infection.",
         "Improve airflow and avoid overhead watering."),
    )),
    ("blotch", Advice(
        "Foliar blotch pathogen. Irregular merging lesions.",
        "routine",
        ("Remove affected leaves and debris.",
         "Protectant fungicide during wet periods.",
         "Improve airflow; rotate."),
    )),
    ("eye spot", Advice(
        "Eye-spot pathogen. Round lesions with pale centres and dark margins.",
        "routine",
        ("Remove affected foliage and fallen debris.",
         "Protectant fungicide on a regular interval.",
         "Shade and airflow management; avoid overhead irrigation."),
    )),
    ("ring spot", Advice(
        "Ringspot. Concentric rings on foliage, viral or fungal depending on host.",
        "routine",
        ("Remove symptomatic plants if a virus is suspected.",
         "Control insect vectors; disinfect tools.",
         "Rotate and use certified seed."),
    )),
    ("brown spot", Advice(
        "Brown spot pathogen. Small dark lesions, worst on older lower leaves.",
        "routine",
        ("Remove lower affected leaves; mulch to stop soil splash.",
         "Protectant fungicide if it moves up the canopy.",
         "Rotate and manage residue."),
    )),
    ("mosaic", Advice(
        "Mosaic virus. Mottled light and dark patterning; no cure.",
        "urgent",
        ("Rogue out infected plants.",
         "Disinfect hands and tools; control aphid vectors.",
         "Certified seed and resistant varieties next season."),
    )),
    ("mold", Advice(
        "Mould pathogen, driven by humidity.",
        "routine",
        ("Ventilate and reduce humidity; space plants.",
         "Remove affected leaves.",
         "Fungicide where an approved product exists."),
    )),
    ("mildew", Advice(
        "Mildew fungus.",
        "routine",
        ("Improve airflow and reduce leaf wetness.",
         "Apply an appropriate fungicide at first symptoms.",
         "Remove affected foliage."),
    )),
)


def _generic_for(normalised: str) -> Advice | None:
    spoken = normalised.replace("_", " ").lower()
    for keyword, advice in GENERIC_BY_KEYWORD:
        if keyword in spoken:
            return advice
    return None


def advice_for(raw_label: str) -> Advice:
    """Look up guidance for a class name, in either the flattened or upstream form."""
    normalised = raw_label.replace("___", "_").replace("__", "_")
    if normalised == "Not_a_leaf":
        return NOT_A_LEAF
    if normalised in ADVICE:
        return ADVICE[normalised]
    if normalised.lower().endswith("healthy"):
        return HEALTHY
    generic = _generic_for(normalised)
    if generic is not None:
        return generic
    return Advice(
        "Disease detected, but no specific entry for this class yet.",
        "routine",
        (
            "Remove and destroy affected leaves and fallen debris.",
            "Improve airflow and avoid overhead irrigation.",
            "Take a clear photo to your local agricultural extension service for confirmation.",
        ),
    )


DISCLAIMER = (
    "General guidance only. Approved products and notification rules vary by country -- "
    "confirm with your local agricultural extension service before applying anything."
)
