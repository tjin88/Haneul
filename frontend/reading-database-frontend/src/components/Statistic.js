import './Statistic.scss';

const Statistic = ({ label, value, label2, value2 }) => {
  return (
    <div className="statistic">
      <h2>
        {label}: <span>{value}</span> |  {label2}: <span>{value2}</span>
      </h2> 
    </div>
  );
};

export default Statistic;
