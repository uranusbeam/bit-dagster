Reusable solids
---------------

Solids are intended to abstract chunks of business logic, but abstractions aren't very meaningful
unless they can be reused.

Our conditional outputs pipeline included a lot of repeated code -- ``sort_hot_cereals_by_calories``
and ``sort_cold_cereals_by_calories``, for instance. In general, it's preferable to build pipelines
out of a relatively restricted set of well-tested library solids, using config liberally to
parametrize them. (You'll certainly have your own version of ``read_csv``, for instance, and
Dagster includes libraries like ``dagster_aws`` and ``dagster_spark`` to wrap and abstract
interfaces with common third party tools.)

Let's replace ``sort_hot_cereals_by_calories`` and ``sort_cold_cereals_by_calories`` by two aliases
of the same library solid:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/reusable_solids.py
   :linenos:
   :lineno-start: 54
   :lines: 54-73
   :emphasize-lines: 17-18
   :caption: reusable_solids.py
   :language: python

You'll see that Dagit distinguishes between the two invocations of the single library solid and the
solid's definition. The invocation is named and bound via a dependency graph to other invocations
of other solids. The definition is the generic, resuable piece of logic that is invoked many times
within this pipeline.

.. thumbnail:: reusable_solids.png

Configuring solids also uses the aliases, as in the following YAML:

.. literalinclude:: ../../../examples/dagster_examples/intro_tutorial/reusable_solids.yaml
   :linenos:
   :emphasize-lines: 6, 8
   :caption: reusable_solids.yaml
   :language: YAML
