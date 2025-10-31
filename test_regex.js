// Тест регулярного выражения для математических выражений
const inlineMathRegex = /(\$[^\$\n]*\$|\\\(.*\)\))/g;

const testCases = [
    "$A = \\pi r^2$",           // Должно совпадать (математическое)
    "\\(x = \\frac{-b}{2a}\\)", // Должно совпадать (математическое)
    "(главный менеджер)",       // НЕ должно совпадать (обычный текст)
    "(специалист по кофе)",     // НЕ должно совпадать (обычный текст)
    "$not math$",              // НЕ должно совпадать (без математических символов)
    "\\(not math\\)",          // НЕ должно совпадать (без математических символов)
];

console.log("Testing inline math regex:");
testCases.forEach(testCase => {
    const matches = testCase.match(inlineMathRegex);
    console.log(`"${testCase}" -> ${matches ? matches.join(', ') : 'no match'}`);
});

// Тест проверки математических символов
console.log("\nTesting math symbol detection:");
testCases.forEach(testCase => {
    const hasMathSymbols = /\\[a-zA-Z]+|[-+=×÷∑∫√^_]/.test(testCase);
    console.log(`"${testCase}" has math symbols: ${hasMathSymbols}`);
});




