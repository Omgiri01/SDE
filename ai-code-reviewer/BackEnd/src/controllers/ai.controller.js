const aiService = require("../services/ai.service");

module.exports.getReview = async (req, res) => {
    const { code } = req.body; // updated for clarity

    if (!code) {
        return res.status(400).send("Prompt is required");
    }

    try {
        const response = await aiService(code);
        res.send(response);
    } catch (error) {
        res.status(500).send("An error occurred while processing the code.");
    }
};
