"""Dutch tests."""

import shutil

import pytest
import pytest_asyncio
from hassil.intents import Intents
from hassil.recognize import recognize
from home_assistant_intents import get_intents
from pysilero_vad import SileroVoiceActivityDetector

from speech_to_phrase import MODELS, Language, Things, train, transcribe
from speech_to_phrase.audio import wav_audio_stream
from speech_to_phrase.hass_api import Area, Entity, Floor

from . import SETTINGS, TESTS_DIR

LANGUAGE = Language.DUTCH.value
MODEL = MODELS[LANGUAGE]

WAV_DIR = TESTS_DIR / "wav" / LANGUAGE

THINGS = Things(
    entities=[
        Entity(names=["New York"], domain="weather"),
        Entity(names=["EcoBee"], domain="climate"),
        Entity(names=["Staande Lamp"], domain="light"),
        Entity(names=["Garagedeur"], domain="cover"),
        Entity(names=["Voordeur"], domain="lock"),
    ],
    areas=[Area(names=["Keuken"]), Area(names=["Kantoor"])],
    floors=[Floor(names=["Eerste Verdieping"])],
)

VAD = SileroVoiceActivityDetector()


@pytest.fixture(scope="session")
def dutch_intents() -> Intents:
    intents_dict = get_intents("nl")
    lists_dict = intents_dict.get("lists", {})
    lists_dict.update(THINGS.to_lists_dict())
    intents_dict["lists"] = lists_dict

    return Intents.from_dict(intents_dict)


@pytest_asyncio.fixture(scope="session")
async def train_dutch() -> None:
    """Train Dutch Kaldi model once per session."""
    if SETTINGS.train_dir.exists():
        shutil.rmtree(SETTINGS.train_dir)

    await train(MODEL, SETTINGS, THINGS)


@pytest.mark.parametrize(
    "text",
    [
        "hoe laat is het",
        "wat is de datum",
        "wat voor weer is het",
        "wat voor weer is het in New York",
        "wat is de temperatuur",
        "wat is de temperatuur van de EcoBee",
        "zet de lampen aan",
        "zet de Staande Lamp aan",
        "doe alle lampen in het Kantoor uit",
        "zet alle lampen op de Eerste Verdieping aan",
        "zet de kleur van de Keuken op groen",
        "zet de helderheid van de Staande Lamp 50 procent",
        "sluit Garagedeur",
        "is de Garagedeur open",
        "vergrendel de Voordeur",
        "is de Voordeur vergrendeld",
        "zet een timer voor 5 minuten",
        "zet een timer voor 30 seconde",
        "zet een timer voor 3 uur en 10 minuten",
        "pauzeer timer",
        "hervat timer",
        "annuleer timer",
        "annuleer alle timers",
        "timer status",
        "pauzeer",
        "hervat",
        "volgende nummer",
        "laat maar",
    ],
)
@pytest.mark.asyncio
async def test_transcribe(
    text: str,
    train_dutch,  # pylint: disable=redefined-outer-name
    dutch_intents: Intents,  # pylint: disable=redefined-outer-name
) -> None:
    """Test transcribing expected sentences."""
    assert recognize(
        text, dutch_intents, intent_context={"area": "Keuken"}
    ), f"Sentence not recognized: {text}"

    # Check transcript
    wav_path = WAV_DIR / f"{text}.wav"
    assert wav_path.exists(), f"Missing {wav_path}"

    transcript = await transcribe(MODEL, SETTINGS, wav_audio_stream(wav_path, VAD))
    assert text == transcript


@pytest.mark.parametrize("wav_num", [1, 2, 3, 4])
@pytest.mark.asyncio
async def test_oov(
    wav_num: int, train_dutch  # pylint: disable=redefined-outer-name
) -> None:
    """Test transcribing out-of-vocabulary (OOV) sentences."""
    wav_path = WAV_DIR / f"oov_{wav_num}.wav"
    assert wav_path.exists(), f"Missing {wav_path}"

    transcript = await transcribe(MODEL, SETTINGS, wav_audio_stream(wav_path, VAD))
    assert not transcript
