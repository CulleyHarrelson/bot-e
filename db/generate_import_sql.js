const fs = require('fs');
const path = require('path');
const { Configuration, OpenAIApi } = require('openai');

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

function get_random_non_empty_dicts_from_json(file_path, num_dicts) {
  const data = JSON.parse(fs.readFileSync(file_path, 'utf8'));

  // Filter out dictionaries with empty question or answer values
  const non_empty_dicts = data.filter(item => item.question && item.answer);

  // Make sure the number of dictionaries to return is not greater than the length of the filtered data
  num_dicts = Math.min(num_dicts, non_empty_dicts.length);

  // Randomly select num_dicts dictionaries from the filtered data
  const random_dicts = non_empty_dicts.sort(() => 0.5 - Math.random()).slice(0, num_dicts);

  return random_dicts;
}

function generate_insert_sql_statements(dictionaries) {
  function processDictionary(dictionary) {
    const question = dictionary.question.replace(/'/g, "''");

    // Call the getEmbeddingData function to get the embedding for the question
    return getEmbeddingData(dictionary.question)
      .then(embeddingData => {
        
        // Check if the embeddingData contains the required data
        if (embeddingData && embeddingData.data && embeddingData.data[0] && Array.isArray(embeddingData.data[0].embedding)) {
          const embedding = embeddingData.data[0].embedding.join(', ');

          // Generate the SQL INSERT statement with both the prompt and the embedding
          const sqlStatement = `INSERT INTO user_prompt (prompt, embedding) VALUES ('${question}', ARRAY[${embedding}]);`;
          return sqlStatement;
        } else {
          console.error('Invalid embedding data:', embeddingData);
          return null;
        }
      })
      .catch(error => {
        // Handle errors, or you can choose to skip this dictionary and continue processing others
        console.error('Error processing dictionary:', dictionary, error);
        return null;
      });
  }

  return Promise.all(dictionaries.map(dictionary => processDictionary(dictionary)));
}

function getEmbeddingData(input) {
  return openai.createEmbedding({
    model: 'text-embedding-ada-002',
    input: input,
  })
    .then(response => {
      return response.data;
    })
    .catch(error => {
      console.error('Error fetching embedding data:', error);
      return null;
    });
}

const file_path = path.join(__dirname, 'sample_data.json');
const num_random_dicts = 50;

const random_dicts = get_random_non_empty_dicts_from_json(file_path, num_random_dicts);

// Call the generate_insert_sql_statements function
generate_insert_sql_statements(random_dicts)
  .then(sqlStatements => {
    const filePath = path.join(__dirname, 'insert_statements.sql');
    const sqlContent = sqlStatements.join('\n');

    // Write the SQL statements to the file
    fs.writeFileSync(filePath, sqlContent);
    console.log('SQL statements saved to insert_statements.sql');
  });
