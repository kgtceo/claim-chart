"""Synthetic, illustrative claim + reference pairs.

All text below is invented for demonstration; it is NOT copied from any real patent or publication.
Educational only — not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleCase:
    name: str
    claim: str
    reference: str
    note: str = ""


SAMPLE_CASES: list[SampleCase] = [
    SampleCase(
        name="anticipated-thermostat",
        claim=(
            "A thermostat control method comprising: measuring an ambient temperature with a "
            "sensor; wherein a target temperature is received from a mobile device over a wireless "
            "link; and activating a heating element when the ambient temperature falls below the "
            "target temperature."
        ),
        reference=(
            "The disclosed climate controller uses a thermistor to measure ambient temperature "
            "with a sensor. A user sets a target temperature which is received from a mobile "
            "device over a wireless link such as Bluetooth. When the measured temperature falls "
            "below the target temperature, the controller responds by activating a heating element "
            "until the setpoint is reached."
        ),
        note="Every limitation is disclosed verbatim — should read as anticipated.",
    ),
    SampleCase(
        name="novel-drone-charging",
        claim=(
            "An unmanned aerial vehicle comprising: a rotor assembly; a battery; a downward-facing "
            "camera for landing; and an inductive charging coil that recharges the battery from a "
            "ground station without physical contact."
        ),
        reference=(
            "The prior-art quadcopter includes a rotor assembly driven by brushless motors and a "
            "rechargeable battery. It carries a downward-facing camera for landing on marked pads. "
            "Recharging is performed by plugging a cable into a wall adapter."
        ),
        note="Rotor, battery and camera are disclosed; the inductive/contactless charging coil is "
        "not — should read as novel over the reference.",
    ),
    SampleCase(
        name="partial-password-manager",
        claim=(
            "A method comprising: storing user credentials in an encrypted vault; deriving an "
            "encryption key from a master passphrase; and synchronising the encrypted vault across "
            "a plurality of devices over a network."
        ),
        reference=(
            "The system stores user credentials in an encrypted vault on the local disk. The vault "
            "is protected by a key that is derived from a master passphrase entered at startup. The "
            "vault is kept only on the single device and is never transmitted."
        ),
        note="Storage and key-derivation are disclosed; cross-device synchronisation is expressly "
        "absent — should read as novel over the reference.",
    ),
]
