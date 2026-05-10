"""Arithmetic circuit definitions for zero-knowledge proofs.

Provides a simple circuit abstraction that can be used to compose more
complex zero-knowledge proofs from elementary gates.  Circuits can be
evaluated directly (for testing) or converted to a Rank-1 Constraint
System (R1CS) representation suitable for integration with proof systems.

Supported gate types:

- **ADD**: Addition of two wires.
- **MUL**: Multiplication of two wires.
- **CONST**: A constant value injected into the circuit.

**R1CS overview**: A Rank-1 Constraint System encodes the circuit as three
matrices ``A``, ``B``, ``C`` such that for a valid witness vector ``w``:

    ``(A * w) . (B * w) = C * w``

where ``.`` denotes element-wise (Hadamard) product.  Each row corresponds
to one constraint derived from a circuit gate.

Only Python stdlib is used -- no external numerical libraries required.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

# ============================================================================
# Gate enum
# ============================================================================


class Gate(Enum):
    """Types of gates in an arithmetic circuit.

    Attributes:
        ADD: Addition gate -- output = left_input + right_input.
        MUL: Multiplication gate -- output = left_input * right_input.
        CONST: Constant gate -- output = constant value (no inputs).
    """

    ADD = "add"
    MUL = "mul"
    CONST = "const"


# ============================================================================
# Wire dataclass
# ============================================================================


@dataclass
class Wire:
    """A wire in an arithmetic circuit carrying a single value.

    Attributes:
        id: Unique identifier for this wire.
        value: The value carried by the wire.  ``None`` until the circuit
            is evaluated.
    """

    id: int
    value: Optional[int] = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Wire):
            return NotImplemented
        return self.id == other.id


# ============================================================================
# _GateEntry (internal)
# ============================================================================


@dataclass
class _GateEntry:
    """Internal representation of a gate within the circuit.

    Attributes:
        gate_type: The operation performed by this gate.
        inputs: Wire IDs serving as inputs.  For ADD and MUL gates this
            is a pair ``[left, right]``.  For CONST gates this is empty.
        output: Wire ID of the gate output.
        constant: The constant value for CONST gates; ``None`` otherwise.
    """

    gate_type: Gate
    inputs: List[int]
    output: int
    constant: Optional[int] = None


# ============================================================================
# ArithmeticCircuit
# ============================================================================


class ArithmeticCircuit:
    """Simple arithmetic circuit for ZK range proofs and sum checks.

    The circuit manages a collection of :class:`Wire` objects connected by
    :class:`Gate` operations.  After construction the circuit can be
    evaluated on concrete inputs and converted to an R1CS representation.

    Example -- verify ``a + b == c``::

        circuit = ArithmeticCircuit()
        w_a = circuit.add_wire()      # wire 0
        w_b = circuit.add_wire()      # wire 1
        w_sum = circuit.add_gate(Gate.ADD, [w_a, w_b])

        result = circuit.evaluate({0: 3, 1: 5})
        assert result[w_sum] == 8

    Example -- range check ``0 <= x <= 10``::

        circuit = ArithmeticCircuit.range_check(0, 10)
        result = circuit.evaluate({0: 5})
        # diff_lo = 5 - 0 = 5 >= 0   (OK)
        # diff_hi = 10 - 5 = 5 >= 0  (OK)
    """

    def __init__(self) -> None:
        self._wires: Dict[int, Wire] = {}
        self._gates: List[_GateEntry] = []
        self._next_wire_id: int = 0
        self._input_wire_ids: List[int] = []

    # ------------------------------------------------------------------
    # Wire management
    # ------------------------------------------------------------------

    def add_wire(self, value: Optional[int] = None) -> int:
        """Create a new input wire and return its ID.

        Args:
            value: Optional initial value for the wire.

        Returns:
            The wire ID (integer).
        """
        wire_id = self._next_wire_id
        self._next_wire_id += 1
        self._wires[wire_id] = Wire(id=wire_id, value=value)
        self._input_wire_ids.append(wire_id)
        return wire_id

    def _allocate_wire(self) -> int:
        """Allocate a new internal (non-input) wire and return its ID."""
        wire_id = self._next_wire_id
        self._next_wire_id += 1
        self._wires[wire_id] = Wire(id=wire_id)
        return wire_id

    @property
    def num_wires(self) -> int:
        """Total number of wires in the circuit."""
        return len(self._wires)

    @property
    def num_gates(self) -> int:
        """Total number of gates in the circuit."""
        return len(self._gates)

    @property
    def input_wire_ids(self) -> List[int]:
        """IDs of all input wires."""
        return list(self._input_wire_ids)

    # ------------------------------------------------------------------
    # Gate management
    # ------------------------------------------------------------------

    def add_gate(
        self,
        gate_type: Gate,
        inputs: List[int],
        output: Optional[int] = None,
        constant: Optional[int] = None,
    ) -> int:
        """Add a gate to the circuit.

        Args:
            gate_type: The operation (ADD, MUL, or CONST).
            inputs: List of input wire IDs.  Must have exactly 2 elements
                for ADD and MUL gates, and 0 elements for CONST gates.
            output: Optional wire ID for the gate output.  If ``None``, a
                new wire is allocated automatically.
            constant: Value for CONST gates; ignored for other gate types.

        Returns:
            Wire ID of the gate output.

        Raises:
            ValueError: If the number of inputs is wrong for the gate type,
                or if an input wire ID does not exist, or if a CONST gate
                has no constant value.
        """
        if gate_type in (Gate.ADD, Gate.MUL):
            if len(inputs) != 2:
                raise ValueError(
                    f"{gate_type.value.upper()} gate requires exactly 2 inputs, got {len(inputs)}."
                )
            for wid in inputs:
                if wid not in self._wires:
                    raise ValueError(f"Wire {wid} does not exist.")
        elif gate_type == Gate.CONST:
            if len(inputs) != 0:
                raise ValueError("CONST gate must have 0 inputs.")
            if constant is None:
                raise ValueError("CONST gate requires a constant value.")

        # Allocate output wire if not specified.
        if output is None:
            out_id = self._allocate_wire()
        else:
            if output not in self._wires:
                out_id = output
                self._wires[out_id] = Wire(id=out_id)
                if out_id >= self._next_wire_id:
                    self._next_wire_id = out_id + 1
            else:
                out_id = output

        entry = _GateEntry(
            gate_type=gate_type,
            inputs=list(inputs),
            output=out_id,
            constant=constant,
        )
        self._gates.append(entry)
        return out_id

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, inputs: Dict[int, int]) -> Dict[int, int]:
        """Evaluate the circuit with concrete input values.

        Processes gates in topological (insertion) order, computing each
        gate's output from its inputs.

        Args:
            inputs: Mapping from input wire ID to integer value.

        Returns:
            Mapping from *every* wire ID to its computed value.

        Raises:
            ValueError: If a required input wire has no value, or if an
                input wire ID does not exist.
        """
        for wid, val in inputs.items():
            if wid not in self._wires:
                raise ValueError(f"Input wire {wid} does not exist.")
            self._wires[wid].value = val

        for gate in self._gates:
            if gate.gate_type == Gate.CONST:
                self._wires[gate.output].value = gate.constant

            elif gate.gate_type == Gate.ADD:
                left = self._wires[gate.inputs[0]].value
                right = self._wires[gate.inputs[1]].value
                if left is None or right is None:
                    raise ValueError(f"ADD gate inputs {gate.inputs} have unset values.")
                self._wires[gate.output].value = left + right

            elif gate.gate_type == Gate.MUL:
                left = self._wires[gate.inputs[0]].value
                right = self._wires[gate.inputs[1]].value
                if left is None or right is None:
                    raise ValueError(f"MUL gate inputs {gate.inputs} have unset values.")
                self._wires[gate.output].value = left * right

        return {wid: w.value for wid, w in self._wires.items() if w.value is not None}

    # ------------------------------------------------------------------
    # R1CS conversion
    # ------------------------------------------------------------------

    def to_r1cs(
        self,
    ) -> Tuple[List[List[int]], List[List[int]], List[List[int]]]:
        """Convert the circuit to a Rank-1 Constraint System.

        Each gate in the circuit becomes one row in the R1CS matrices.
        The witness vector ``w`` is ordered as::

            w = [1, wire_0, wire_1, ..., wire_n]

        where index 0 is the constant-one element.

        Encoding rules:

        - **ADD**: ``(left + right) * 1 = output``
        - **MUL**: ``left * right = output``
        - **CONST**: ``constant * 1 = output``

        Returns:
            Tuple ``(A, B, C)`` where each element is a list of rows.
            Each row is a list of integer coefficients of length
            ``num_wires + 1`` (to accommodate the constant column).

        Raises:
            RuntimeError: If the circuit has no gates.
        """
        if not self._gates:
            raise RuntimeError("Circuit has no gates; cannot produce R1CS.")

        n = self.num_wires + 1  # +1 for the constant column (index 0)
        A: List[List[int]] = []
        B: List[List[int]] = []
        C: List[List[int]] = []

        for gate in self._gates:
            a_row = [0] * n
            b_row = [0] * n
            c_row = [0] * n

            out_idx = gate.output + 1  # offset by 1 for constant column

            if gate.gate_type == Gate.MUL:
                # Constraint: left * right = output
                left_idx = gate.inputs[0] + 1
                right_idx = gate.inputs[1] + 1
                a_row[left_idx] = 1
                b_row[right_idx] = 1
                c_row[out_idx] = 1

            elif gate.gate_type == Gate.ADD:
                # Constraint: (left + right) * 1 = output
                left_idx = gate.inputs[0] + 1
                right_idx = gate.inputs[1] + 1
                a_row[left_idx] = 1
                a_row[right_idx] = 1
                b_row[0] = 1  # constant 1
                c_row[out_idx] = 1

            elif gate.gate_type == Gate.CONST:
                # Constraint: constant * 1 = output
                a_row[0] = gate.constant if gate.constant is not None else 0
                b_row[0] = 1
                c_row[out_idx] = 1

            A.append(a_row)
            B.append(b_row)
            C.append(c_row)

        return A, B, C

    # ------------------------------------------------------------------
    # R1CS witness verification
    # ------------------------------------------------------------------

    @staticmethod
    def verify_r1cs(
        A: List[List[int]],
        B: List[List[int]],
        C: List[List[int]],
        witness: List[int],
    ) -> bool:
        """Check that a witness vector satisfies the R1CS constraints.

        Verifies that for every row ``i``::

            dot(A[i], w) * dot(B[i], w) == dot(C[i], w)

        Args:
            A: Matrix A from :meth:`to_r1cs`.
            B: Matrix B from :meth:`to_r1cs`.
            C: Matrix C from :meth:`to_r1cs`.
            witness: Witness vector ``[1, wire_0, wire_1, ...]``.

        Returns:
            ``True`` if all constraints are satisfied.
        """
        for i in range(len(A)):
            a_dot = sum(a * w for a, w in zip(A[i], witness))
            b_dot = sum(b * w for b, w in zip(B[i], witness))
            c_dot = sum(c * w for c, w in zip(C[i], witness))
            if a_dot * b_dot != c_dot:
                return False
        return True

    # ------------------------------------------------------------------
    # Convenience: range check circuit
    # ------------------------------------------------------------------

    @classmethod
    def range_check(cls, lower: int, upper: int) -> ArithmeticCircuit:
        """Build a circuit that checks ``lower <= x <= upper``.

        The circuit computes:

        - ``diff_lo = x - lower``  (should be >= 0)
        - ``diff_hi = upper - x``  (should be >= 0)
        - ``product = diff_lo * diff_hi``  (>= 0 iff both diffs >= 0)

        Args:
            lower: Inclusive lower bound.
            upper: Inclusive upper bound.

        Returns:
            An :class:`ArithmeticCircuit` with one input wire (ID 0).

        Raises:
            ValueError: If ``lower > upper``.
        """
        if lower > upper:
            raise ValueError(f"lower ({lower}) > upper ({upper})")

        circuit = cls()
        w_x = circuit.add_wire()  # wire 0: input x

        # Constant: -lower
        w_neg_lower = circuit.add_gate(Gate.CONST, [], constant=-lower)
        # diff_lo = x + (-lower) = x - lower
        w_diff_lo = circuit.add_gate(Gate.ADD, [w_x, w_neg_lower])

        # Constant: upper
        w_upper = circuit.add_gate(Gate.CONST, [], constant=upper)
        # Constant: -1
        w_neg1 = circuit.add_gate(Gate.CONST, [], constant=-1)
        # neg_x = x * (-1)
        w_neg_x = circuit.add_gate(Gate.MUL, [w_x, w_neg1])
        # diff_hi = upper + neg_x = upper - x
        w_diff_hi = circuit.add_gate(Gate.ADD, [w_upper, w_neg_x])

        # product = diff_lo * diff_hi
        circuit.add_gate(Gate.MUL, [w_diff_lo, w_diff_hi])

        return circuit

    @classmethod
    def sum_check(cls, n_inputs: int) -> ArithmeticCircuit:
        """Build a circuit that computes the sum of *n_inputs* values.

        The resulting circuit has ``n_inputs`` input wires (IDs 0 through
        ``n_inputs - 1``).  After evaluation the last allocated wire
        contains the sum of all inputs.

        Args:
            n_inputs: Number of input values to sum.

        Returns:
            An :class:`ArithmeticCircuit`.

        Raises:
            ValueError: If ``n_inputs < 1``.
        """
        if n_inputs < 1:
            raise ValueError("n_inputs must be at least 1.")

        circuit = cls()
        wire_ids: List[int] = []
        for _ in range(n_inputs):
            wire_ids.append(circuit.add_wire())

        if n_inputs == 1:
            w_zero = circuit.add_gate(Gate.CONST, [], constant=0)
            circuit.add_gate(Gate.ADD, [wire_ids[0], w_zero])
        else:
            acc = circuit.add_gate(Gate.ADD, [wire_ids[0], wire_ids[1]])
            for i in range(2, n_inputs):
                acc = circuit.add_gate(Gate.ADD, [acc, wire_ids[i]])

        return circuit
