import Section from "/src/common/Section";
import Flex from "/src/common/Flex";
import "./TestFlex.scss"


const TestFlex = (props) => {
    const words = [
        "Eins", "Zwei", "Drei", "Vier", "Fünf", "Sechs", "Sieben", "Acht", "Neun", "Zehn",
    ];
    return (
        <div className={"test-flex-container"}>
            <Section title={"flex test"}>
                <h4>row</h4>
                <Flex>
                    {words.map(w => <Flex.Item key={w}>{w}</Flex.Item>)}
                </Flex>

                <h4>column</h4>
                <Flex column>
                    {words.map(w => <Flex.Item key={w}>{w}</Flex.Item>)}
                </Flex>

                <h4>grow</h4>
                <Flex.Row>
                    <Flex.Item>normal</Flex.Item>
                    <Flex.Item grow={1}>grow 1</Flex.Item>
                    <Flex.Item grow={2}>grow 2</Flex.Item>
                    <Flex.Item shrink>shrink</Flex.Item>
                </Flex.Row>

                <h4>justify</h4>
                <div className={"box"} style={{width: "10rem"}}>
                    <Flex justify={"start"}><Flex.Item>start</Flex.Item></Flex>
                    <Flex justify={"center"}><Flex.Item>center</Flex.Item></Flex>
                    <Flex justify={"end"}><Flex.Item>end</Flex.Item></Flex>
                    <Flex justify={"space-between"}>
                        <Flex.Item>some</Flex.Item>
                        <Flex.Item>space</Flex.Item>
                        <Flex.Item>between</Flex.Item>
                    </Flex>
                    <Flex justify={"space-evenly"}>
                        <Flex.Item>some</Flex.Item>
                        <Flex.Item>space</Flex.Item>
                        <Flex.Item>evenly</Flex.Item>
                    </Flex>
                    <Flex justify={"space-around"}>
                        <Flex.Item>some</Flex.Item>
                        <Flex.Item>space</Flex.Item>
                        <Flex.Item>around</Flex.Item>
                    </Flex>
                </div>

                <h4>margin</h4>
                <div className={"box"} style={{width: "10rem"}}>
                    <Flex wrap marginX={".1rem"} marginY={".4rem"}
                          //justify={"center"}
                    >
                        {words.map(w => <Flex.Item key={w} grow={w === "Fünf"}>{w}</Flex.Item>)}
                    </Flex>
                </div>
            </Section>
        </div>
    );
}

export default TestFlex;