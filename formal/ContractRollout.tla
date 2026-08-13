-------------------------- MODULE ContractRollout --------------------------
EXTENDS Integers, TLC

CONSTANTS Consumers, Versions
VARIABLES published, supported

vars == <<published, supported>>

Init ==
  /\ published = 1
  /\ supported = [consumer \in Consumers |-> 1]

Upgrade(consumer) ==
  /\ supported[consumer] = 1
  /\ supported' = [supported EXCEPT ![consumer] = 2]
  /\ UNCHANGED published

Publish ==
  /\ \A consumer \in Consumers : supported[consumer] >= 2
  /\ published' = 2
  /\ UNCHANGED supported

UnsafePublish ==
  /\ published' = 2
  /\ UNCHANGED supported

SafeNext ==
  \/ \E consumer \in Consumers : Upgrade(consumer)
  \/ Publish

UnsafeNext ==
  \/ \E consumer \in Consumers : Upgrade(consumer)
  \/ UnsafePublish

SafeSpec ==
  /\ Init
  /\ [][SafeNext]_vars
  /\ \A consumer \in Consumers : WF_vars(Upgrade(consumer))
  /\ WF_vars(Publish)

UnsafeSpec == Init /\ [][UnsafeNext]_vars

TypeOK ==
  /\ published \in Versions
  /\ supported \in [Consumers -> Versions]

NoUnsupportedConsumer ==
  \A consumer \in Consumers : published <= supported[consumer]

EventuallyVersionTwo == <>(published = 2)

=============================================================================

