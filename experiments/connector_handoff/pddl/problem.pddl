(define (problem connector_nominal)
    (:domain connector_assembly)
    (:objects
        robot - agent
        connector - connector
        socket - socket
    )
    (:init
        (available connector)
        (handempty robot)
        (inview robot connector)
        (inview robot socket)
        (side_clear_left socket)
        (side_clear_right socket)
    )

    (:goal
        (and (inserted connector socket))
    )
)
