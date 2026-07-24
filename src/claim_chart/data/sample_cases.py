"""Illustrative claim + reference pairs.

Synthetic cases are invented for demonstration. One case uses the claim of a REAL granted
(and long-expired) patent — US 5,960,411, Amazon's "1-Click" patent — against a synthetic
description of a conventional shopping-cart system; it is tagged as such. Patents are public
documents. Educational only — not legal advice.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SampleCase:
    name: str
    claim: str
    reference: str
    note: str = ""
    tag: str = ""


SAMPLE_CASES: list[SampleCase] = [
    SampleCase(
        name="real-patent-us5960411-oneclick",
        claim=(
            "A method of placing an order for an item comprising: under control of a client "
            "system, displaying information identifying the item; and in response to only a "
            "single action being performed, sending a request to order the item along with an "
            "identifier of a purchaser of the item to a server system; under control of a "
            "single-action ordering component of the server system, receiving the request; "
            "retrieving additional information previously stored for the purchaser identified by "
            "the identifier in the received request; and generating an order to purchase the "
            "requested item for the purchaser identified by the identifier in the received "
            "request using the retrieved additional information; and fulfilling the generated "
            "order to complete purchase of the item whereby the item is ordered without using a "
            "shopping cart ordering model."
        ),
        reference=(
            "The prior-art online shopping system operates as follows. Under control of a client "
            "system, the browser displays information identifying the item on a product page. To "
            "purchase, the shopper first adds the item to a shopping cart, then proceeds through "
            "a multi-step checkout with several confirmation pages. During checkout, the client "
            "sends a request to order the item along with an identifier of a purchaser of the "
            "item to a server system. The server system receives the request, and retrieves "
            "additional information previously stored for the purchaser, such as a shipping "
            "address and payment details, from the purchaser's account. The server then "
            "generates an order to purchase the requested item using the retrieved information, "
            "and the order is fulfilled once the shopper confirms the final checkout summary "
            "page."
        ),
        note=(
            "Claim 1 of US 5,960,411 (Amazon '1-Click', granted 1999, expired) charted against a "
            "synthetic conventional shopping-cart system. The generic steps are disclosed — but "
            "every limitation tied to single-action ordering ('in response to only a single "
            "action', the 'single-action ordering component', ordering 'without using a shopping "
            "cart') is not. Should read as novel over the reference (which is roughly why the "
            "patent was granted)."
        ),
        tag="Real patent claim · US 5,960,411 · expired",
    ),
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
        name="novel-password-manager-sync",
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
