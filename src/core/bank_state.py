"""Bank state - resource pool and development cards"""
from ..simulator.types.resource import ResourceType, DevelopmentCardType, ResourceCount, DevelopmentCardCount


class BankState:
    """Bank resource pool and development card deck"""
    def __init__(self):
        # Standard Catan bank has 19 of each resource
        self.resources: ResourceCount = {
            ResourceType.WOOD: 19,
            ResourceType.BRICK: 19,
            ResourceType.SHEEP: 19,
            ResourceType.WHEAT: 19,
            ResourceType.ORE: 19,
        }
        
        # Development card deck
        # Standard Catan has: 14 knights, 2 road building, 2 year of plenty, 
        # 2 monopoly, 5 victory points = 25 total
        self.development_cards: DevelopmentCardCount = {
            DevelopmentCardType.KNIGHT: 14,
            DevelopmentCardType.ROAD_BUILDING: 2,
            DevelopmentCardType.YEAR_OF_PLENTY: 2,
            DevelopmentCardType.MONOPOLY: 2,
            DevelopmentCardType.VICTORY_POINT: 5,
        }

    def get_total_resources(self) -> int:
        """Get total resource cards in bank"""
        return sum(self.resources.values())

    def get_total_development_cards(self) -> int:
        """Get total development cards in deck"""
        return sum(self.development_cards.values())

    def has_resource(self, resource_type: ResourceType, amount: int = 1) -> bool:
        """Check if bank has enough of a resource"""
        return self.resources[resource_type] >= amount

    def has_development_card(self, card_type: DevelopmentCardType) -> bool:
        """Check if bank has a development card"""
        return self.development_cards[card_type] > 0

    def __repr__(self):
        return (f"BankState(resources={self.get_total_resources()}, "
                f"devCards={self.get_total_development_cards()})")
