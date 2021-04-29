package com.mpds.simulator.domain.model.bins.iterfirst;

import com.mpds.simulator.domain.model.Coordinate;
import com.mpds.simulator.domain.model.Person;
import com.mpds.simulator.domain.model.bins.BottomBin;
import com.mpds.simulator.port.adapter.kafka.DomainEventPublisher;

public class BottomBinIterFirst extends BottomBin {

    public BottomBinIterFirst(DomainEventPublisher domainEventPublisher, Coordinate ulCorner, Coordinate lrCorner){
        super(domainEventPublisher, ulCorner, lrCorner);
    }

    @Override
    public void findInteractionsWithNeighbours(long time, Person person) {
        Coordinate pos = person.getPos();

        if (isOverlapAboveLeft(pos)){
            aboveLeft.interactionWithPeople(time, person);
        }
        if (isOverlapAbove(pos)){
            above.interactionWithPeople(time, person);
        }
        if (isOverlapAboveRight(pos)){
            aboveRight.interactionWithPeople(time, person);
        }
        if (isOverlapRight(pos)) {
            right.interactionWithPeople(time, person);
        }
    }
}
