import './Statistic.scss';

const Statistic = ({ label, value }) => {
  return (
    <div className="statistic">
      <h2>{label}: <span>{value}</span></h2>
    </div>
  );
};

export default Statistic;
